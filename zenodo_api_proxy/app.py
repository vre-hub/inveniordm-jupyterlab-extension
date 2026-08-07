"""
Auth-only MVP for the Zenodo API proxy.

This deliberately keeps browser session state in memory and only proves the
OAuth login flow against the Zenodo sandbox.
"""

from __future__ import annotations

import secrets
import sys
from http import HTTPStatus

import tornado.httpserver
import tornado.ioloop
import tornado.web

from zenodo_auth import OAuthCallback, OAuthClientConfig
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

PROXY_TOKEN_REMOTE_SERVER_ID = "REMOTE"


class HealthHandler(BaseProxyHandler):
    def get(self) -> None:
        self.write_json({"ok": True, "zenodo_base_url": self.config.zenodo_base_url})


class LoginHandler(BaseProxyHandler):
    def get(self) -> None:
        begin_zenodo_oauth_login(
            self,
            oauth_config=self.oauth_config,
            save_oauth_state=self.state.oauth_states.__setitem__,
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
            oauth_config=self.oauth_config,
            pop_oauth_state=lambda state: self.state.oauth_states.pop(state, None),
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
        remote_server_id=PROXY_TOKEN_REMOTE_SERVER_ID,
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
    oauth_config: OAuthClientConfig | None = None,
    token_store: MultiTokenStore | None = None,
) -> tornado.web.Application:
    proxy_state = state or ProxyState()
    zenodo_token_store = token_store or FileTokenStore()
    zenodo_oauth_config = oauth_config or OAuthClientConfig(
        zenodo_base_url=config.zenodo_base_url,
        client_id=config.client_id,
        client_secret=config.client_secret,
        redirect_uri=config.redirect_uri,
        scope=config.scope,
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
        zenodo_oauth_config=zenodo_oauth_config,
        zenodo_token_store=zenodo_token_store,
    )


def create_server(
    config: Config,
    host: str,
    port: int,
    state: ProxyState | None = None,
    oauth_config: OAuthClientConfig | None = None,
    token_store: MultiTokenStore | None = None,
) -> tornado.httpserver.HTTPServer:
    app = create_app(config, state, oauth_config, token_store)
    server = tornado.httpserver.HTTPServer(
        app,
        # ApiProxyHandler streams request bodies, so no file-size-dependent
        # application limit or equivalent in-memory allocation is needed.
        max_body_size=sys.maxsize,
    )
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
