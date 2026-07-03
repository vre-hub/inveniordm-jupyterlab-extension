import json
import os
from urllib.parse import urlparse

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from tornado.web import RequestHandler

from zenodo_auth import OAuthCallback, OAuthClientConfig
from zenodo_auth.token_store import BoundedTokenStore
from zenodo_auth.tornado_oauth import (
    begin_zenodo_oauth_login,
    finish_zenodo_oauth_callback,
)

from ..zenodo_requests.zenodo_requests_factory import get_sandbox_override

SANDBOX_OAUTH_CLIENT_ID = "ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU"
PRODUCTION_OAUTH_CLIENT_ID = "HaWBPRb7lsif7cqTypUNeFni9PJOoTm5IcjTJrtt"
OAUTH_SCOPE = "deposit:write deposit:actions"


class LocalZenodoAuthController:
    production_url = "https://zenodo.org"
    sandbox_url = "https://sandbox.zenodo.org"

    def __init__(self, token_store: BoundedTokenStore):
        self.token_store = token_store

        # key: (sandbox, redirect_uri)
        self.oauth_configs: dict[tuple[bool, str], OAuthClientConfig] = {}
        self.oauth_states: dict[str, tuple[str, bool, str]] = {}

    def login(self, handler: APIHandler) -> None:
        sandbox = self._oauth_sandbox(handler)
        oauth_config = self._oauth_config(handler, sandbox)
        begin_zenodo_oauth_login(
            handler,
            oauth_config=oauth_config,
            save_oauth_state=lambda state, return_to: self._save_oauth_state(
                state,
                return_to,
                sandbox=sandbox,
                redirect_uri=oauth_config.redirect_uri,
            ),
            default_return_to=self._default_return_to(handler),
            is_allowed_return_to=lambda return_to: self._is_allowed_return_to(
                handler,
                return_to,
            ),
        )

    def logout(self, handler: APIHandler) -> None:
        self.token_store.remove_token()
        return_to = handler.get_query_argument("return_to", None)
        if return_to is not None:
            if not self._is_allowed_return_to(handler, return_to):
                handler.set_status(400)
                handler.finish(json.dumps({"message": "Invalid return_to URL"}))
                return
            handler.redirect(return_to)
            return
        handler.finish(json.dumps({"authenticated": False}))

    def callback(self, handler: APIHandler) -> None:
        oauth_config, sandbox = self._oauth_config_for_callback(handler)
        finish_zenodo_oauth_callback(
            handler,
            oauth_config=oauth_config,
            pop_oauth_state=self._pop_return_to,
            on_success=lambda callback_handler, callback: (
                self._complete_oauth_login(
                    callback_handler,
                    callback,
                    sandbox=sandbox,
                )
            ),
        )

    def _complete_oauth_login(
        self,
        handler: RequestHandler,
        callback: OAuthCallback,
        *,
        sandbox: bool,
    ) -> None:
        self.token_store.set_token(
            callback.access_token,
            True,
            sandbox=sandbox,
        )
        handler.redirect(callback.return_to)

    def _oauth_config(self, handler: APIHandler, sandbox: bool) -> OAuthClientConfig:
        redirect_uri = self._oauth_callback_url(handler)
        key = (sandbox, redirect_uri)
        client_id = SANDBOX_OAUTH_CLIENT_ID if sandbox else PRODUCTION_OAUTH_CLIENT_ID
        if key not in self.oauth_configs:
            self.oauth_configs[key] = OAuthClientConfig(
                zenodo_base_url=self._server_url(sandbox),
                client_id=client_id,
                redirect_uri=redirect_uri,
                scope=OAUTH_SCOPE,
            )
        return self.oauth_configs[key]

    def _oauth_config_for_callback(
        self,
        handler: APIHandler,
    ) -> tuple[OAuthClientConfig, bool]:
        state = handler.get_query_argument("state", None)
        if state in self.oauth_states:
            _, sandbox, redirect_uri = self.oauth_states[state]
            return self.oauth_configs[(sandbox, redirect_uri)], sandbox

        sandbox = self._oauth_sandbox(handler)
        return self._oauth_config(handler, sandbox), sandbox

    def _save_oauth_state(
        self,
        state: str,
        return_to: str,
        *,
        sandbox: bool,
        redirect_uri: str,
    ) -> None:
        self.oauth_states[state] = (return_to, sandbox, redirect_uri)

    def _pop_return_to(self, state: str) -> str | None:
        stored_state = self.oauth_states.pop(state, None)
        if stored_state is None:
            return None
        return stored_state[0]

    def _oauth_sandbox(self, handler: APIHandler) -> bool:
        sandbox_override = get_sandbox_override(handler)
        return sandbox_override if sandbox_override is not None else False

    def _server_url(self, sandbox: bool) -> str:
        return self.sandbox_url if sandbox else self.production_url

    def _public_url(self, handler: APIHandler) -> str:
        return os.environ.get(
            "ZENODO_JUPYTERLAB_PUBLIC_URL",
            f"{handler.request.protocol}://{handler.request.host}",
        ).rstrip("/")

    def _oauth_callback_url(self, handler: APIHandler) -> str:
        return url_path_join(
            self._public_url(handler),
            handler.settings["base_url"],
            "zenodo-jupyterlab",
            "auth",
            "callback",
        )

    def _default_return_to(self, handler: APIHandler) -> str:
        return handler.request.headers.get(
            "Referer",
            url_path_join(
                self._public_url(handler),
                handler.settings["base_url"],
                "lab",
            ),
        )

    def _is_allowed_return_to(self, handler: APIHandler, return_to: str) -> bool:
        parsed = urlparse(return_to)
        if parsed.scheme not in {"http", "https"}:
            return False

        allowed_hosts = {"localhost", "127.0.0.1", "::1"}
        public_host = urlparse(self._public_url(handler)).hostname
        if public_host:
            allowed_hosts.add(public_host)

        extra_hosts = os.environ.get("ZENODO_JUPYTERLAB_ALLOWED_RETURN_HOSTS")
        if extra_hosts:
            allowed_hosts.update(
                host.strip() for host in extra_hosts.split(",") if host.strip()
            )

        return parsed.hostname in allowed_hosts
