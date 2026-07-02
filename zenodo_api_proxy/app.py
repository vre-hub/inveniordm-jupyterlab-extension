"""
Auth-only MVP for the Zenodo API proxy.

This deliberately keeps browser session state in memory and only proves the
OAuth login flow against the Zenodo sandbox.
"""

from __future__ import annotations

import secrets
from http import HTTPStatus
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

import tornado.httpserver
import tornado.ioloop
import tornado.web

from zenodo_auth.auth_service import (
    OAuthConfigurationError,
    OAuthStateError,
    OAuthTokenResponseError,
    ZenodoAuthService,
)
from zenodo_auth.token_store import FileTokenStore

from .api_proxy_handler import ApiProxyHandler
from .base_handler import BaseProxyHandler
from .config import Config
from .helpers import is_allowed_return_to
from .logout_handler import LogoutHandler
from .status_handler import StatusHandler
from .types import ProxyState


class HealthHandler(BaseProxyHandler):
    def get(self) -> None:
        self.write_json({"ok": True, "zenodo_base_url": self.config.zenodo_base_url})


class LoginHandler(BaseProxyHandler):
    def get(self) -> None:
        return_to = self.get_query_argument("return_to", self.config.proxy_public_url)
        if not is_allowed_return_to(return_to, self.config):
            self.write_json({"message": "Invalid return_to URL"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            login = self.auth_service.begin_login(return_to)
        except OAuthConfigurationError as error:
            self.write_json(
                {"message": str(error)},
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        self.set_proxy_cookie(
            self.config.oauth_state_cookie_name,
            login.state,
            max_age=600,
            same_site="Lax",
        )
        self.redirect(login.authorize_url)


class CallbackHandler(BaseProxyHandler):
    def get(self) -> None:
        error = self.get_query_argument("error", None)
        if error:
            self.write_json(
                {"message": f"Zenodo OAuth returned an error: {error}"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        code = self.get_query_argument("code", None)
        state = self.get_query_argument("state", None)
        if not code or not state:
            self.write_json({"message": "Missing code or state"}, HTTPStatus.BAD_REQUEST)
            return

        if self.get_cookie(self.config.oauth_state_cookie_name) != state:
            self.write_json(
                {"message": "OAuth state cookie mismatch"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            callback = self.auth_service.finish_login(code=code, state=state)
        except OAuthStateError as error:
            self.write_json({"message": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        except OAuthTokenResponseError as error:
            self.write_json(
                {"message": str(error)},
                HTTPStatus.BAD_GATEWAY,
            )
            return
        except HTTPError as error:
            self.write_json(
                {
                    "message": "Zenodo OAuth request failed",
                    "status": error.code,
                    "body": error.read().decode("utf-8", errors="replace"),
                },
                HTTPStatus.BAD_GATEWAY,
            )
            return
        except URLError as error:
            self.write_json(
                {"message": f"Could not reach Zenodo: {error.reason}"},
                HTTPStatus.BAD_GATEWAY,
            )
            return

        session_id = secrets.token_urlsafe(32)
        self.state.sessions[session_id] = callback.zenodo_user_id
        self.set_proxy_cookie(
            self.config.session_cookie_name,
            session_id,
            max_age=60 * 60 * 24 * 14,
            same_site="Lax",
        )
        self.expire_proxy_cookie(self.config.oauth_state_cookie_name)
        self.redirect(callback.return_to)


class JsonNotFoundHandler(BaseProxyHandler):
    def prepare(self) -> None:
        self.write_json({"message": "Not found"}, HTTPStatus.NOT_FOUND)


def create_app(
    config: Config,
    state: ProxyState | None = None,
    auth_service: ZenodoAuthService | None = None,
) -> tornado.web.Application:
    proxy_state = state or ProxyState()
    zenodo_auth_service = auth_service or ZenodoAuthService(
        zenodo_base_url=config.zenodo_base_url,
        client_id=config.client_id,
        client_secret=config.client_secret,
        redirect_uri=config.redirect_uri,
        scope=config.scope,
        token_store=FileTokenStore(),
        sandbox="sandbox.zenodo.org" in urlparse(config.zenodo_base_url).netloc,
    )
    return tornado.web.Application(
        [
            (r"/health", HealthHandler),
            (r"/auth/login", LoginHandler),
            (r"/auth/callback", CallbackHandler),
            (r"/auth/status", StatusHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/api(/.*)?", ApiProxyHandler),
            (r"/.*", JsonNotFoundHandler),
        ],
        proxy_config=config,
        proxy_state=proxy_state,
        zenodo_auth_service=zenodo_auth_service,
    )


def create_server(
    config: Config,
    host: str,
    port: int,
    state: ProxyState | None = None,
    auth_service: ZenodoAuthService | None = None,
) -> tornado.httpserver.HTTPServer:
    app = create_app(config, state, auth_service)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port, address=host)
    return server


def main() -> None:
    config = Config.from_environment()
    create_server(config, config.proxy_host, config.proxy_port)
    print(
        "Zenodo API proxy MVP listening on "
        f"http://{config.proxy_host}:{config.proxy_port}"
    )
    print(f"Zenodo base URL: {config.zenodo_base_url}")
    print(f"OAuth redirect URI: {config.redirect_uri}")
    tornado.ioloop.IOLoop.current().start()
