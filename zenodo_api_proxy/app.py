"""
Auth-only MVP for the Zenodo API proxy.

This deliberately keeps browser session state in memory and only proves the
OAuth login flow against the Zenodo sandbox.
"""

from __future__ import annotations

import secrets
from http import HTTPStatus
from urllib.parse import urlparse

import tornado.httpserver
import tornado.ioloop
import tornado.web

from zenodo_auth.auth_service import OAuthCallback, ZenodoAuthService
from zenodo_auth.token_store import FileTokenStore, MultiTokenStore
from zenodo_auth.tornado_oauth import (
    begin_zenodo_oauth_login,
    finish_zenodo_oauth_callback,
)

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
        begin_zenodo_oauth_login(
            self,
            auth_service=self.auth_service,
            default_return_to=self.config.proxy_public_url,
            is_allowed_return_to=lambda return_to: is_allowed_return_to(
                return_to,
                self.config,
            ),
            state_cookie_name=self.config.oauth_state_cookie_name,
        )


class CallbackHandler(BaseProxyHandler):
    def get(self) -> None:
        finish_zenodo_oauth_callback(
            self,
            auth_service=self.auth_service,
            on_success=complete_proxy_login,
            state_cookie_name=self.config.oauth_state_cookie_name,
        )


class JsonNotFoundHandler(BaseProxyHandler):
    def prepare(self) -> None:
        self.write_json({"message": "Not found"}, HTTPStatus.NOT_FOUND)


def complete_proxy_login(
    handler: tornado.web.RequestHandler,
    callback: OAuthCallback,
) -> None:
    config: Config = handler.settings["proxy_config"]
    state: ProxyState = handler.settings["proxy_state"]
    token_store: MultiTokenStore = handler.settings["zenodo_token_store"]

    token_store.set_token(
        callback.zenodo_user_id,
        callback.access_token,
        True,
        sandbox="sandbox.zenodo.org" in urlparse(config.zenodo_base_url).netloc,
    )

    session_id = secrets.token_urlsafe(32)
    state.sessions[session_id] = callback.zenodo_user_id
    handler.set_cookie(
        config.session_cookie_name,
        session_id,
        path="/",
        max_age=60 * 60 * 24 * 14,
        httponly=True,
        samesite="Lax",
    )
    handler.redirect(callback.return_to)


def create_app(
    config: Config,
    state: ProxyState | None = None,
    auth_service: ZenodoAuthService | None = None,
    token_store: MultiTokenStore | None = None,
) -> tornado.web.Application:
    proxy_state = state or ProxyState()
    zenodo_token_store = token_store or FileTokenStore()
    zenodo_auth_service = auth_service or ZenodoAuthService(
        zenodo_base_url=config.zenodo_base_url,
        client_id=config.client_id,
        client_secret=config.client_secret,
        redirect_uri=config.redirect_uri,
        scope=config.scope,
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
        zenodo_token_store=zenodo_token_store,
    )


def create_server(
    config: Config,
    host: str,
    port: int,
    state: ProxyState | None = None,
    auth_service: ZenodoAuthService | None = None,
    token_store: MultiTokenStore | None = None,
) -> tornado.httpserver.HTTPServer:
    app = create_app(config, state, auth_service, token_store)
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
