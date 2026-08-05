import json
import os
from urllib.parse import urlparse

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from tornado.web import RequestHandler

from zenodo_auth import OAuthCallback, OAuthClientConfig
from zenodo_auth.remote_servers import (
    RemoteServerId,
    get_remote_server,
)
from zenodo_auth.token_store import BoundedTokenStore
from zenodo_auth.tornado_oauth import (
    begin_zenodo_oauth_login,
    finish_zenodo_oauth_callback,
)

from ..zenodo_requests.zenodo_requests_factory import get_remote_server_override

OAUTH_SCOPE = "deposit:write deposit:actions"


class LocalZenodoAuthController:
    def __init__(self, token_store: BoundedTokenStore):
        self.token_store = token_store

        self.oauth_configs: dict[tuple[RemoteServerId, str], OAuthClientConfig] = {}
        self.oauth_states: dict[str, tuple[str, RemoteServerId, str]] = {}

    def login(self, handler: APIHandler) -> None:
        remote_server_id = self._oauth_remote_server_id(handler)
        oauth_config = self._oauth_config(handler, remote_server_id)
        begin_zenodo_oauth_login(
            handler,
            oauth_config=oauth_config,
            save_oauth_state=lambda state, return_to: self._save_oauth_state(
                state,
                return_to,
                remote_server_id=remote_server_id,
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
        oauth_config, remote_server_id = self._oauth_config_for_callback(handler)
        finish_zenodo_oauth_callback(
            handler,
            oauth_config=oauth_config,
            pop_oauth_state=self._pop_return_to,
            on_success=lambda callback_handler, callback: self._complete_oauth_login(
                callback_handler,
                callback,
                remote_server_id=remote_server_id,
            ),
        )

    def _complete_oauth_login(
        self,
        handler: RequestHandler,
        callback: OAuthCallback,
        *,
        remote_server_id: RemoteServerId,
    ) -> None:
        self.token_store.set_token(
            callback.access_token,
            True,
            remote_server_id=remote_server_id,
            zenodo_user_id=callback.zenodo_user_id,
        )
        handler.redirect(callback.return_to)

    def _oauth_config(
        self, handler: APIHandler, remote_server_id: RemoteServerId
    ) -> OAuthClientConfig:
        redirect_uri = self._oauth_callback_url(handler)
        key = (remote_server_id, redirect_uri)
        server = get_remote_server(remote_server_id)
        if key not in self.oauth_configs:
            self.oauth_configs[key] = OAuthClientConfig(
                zenodo_base_url=server.base_url,
                client_id=server.oauth_client_id,
                redirect_uri=redirect_uri,
                scope=OAUTH_SCOPE,
            )
        return self.oauth_configs[key]

    def _oauth_config_for_callback(
        self,
        handler: APIHandler,
    ) -> tuple[OAuthClientConfig, RemoteServerId]:
        state = handler.get_query_argument("state", None)
        if state in self.oauth_states:
            _, remote_server_id, redirect_uri = self.oauth_states[state]
            return self.oauth_configs[
                (remote_server_id, redirect_uri)
            ], remote_server_id

        remote_server_id = self._oauth_remote_server_id(handler)
        return self._oauth_config(handler, remote_server_id), remote_server_id

    def _save_oauth_state(
        self,
        state: str,
        return_to: str,
        *,
        remote_server_id: RemoteServerId,
        redirect_uri: str,
    ) -> None:
        self.oauth_states[state] = (return_to, remote_server_id, redirect_uri)

    def _pop_return_to(self, state: str) -> str | None:
        stored_state = self.oauth_states.pop(state, None)
        if stored_state is None:
            return None
        return stored_state[0]

    def _oauth_remote_server_id(self, handler: APIHandler) -> RemoteServerId:
        return get_remote_server_override(handler) or RemoteServerId.ZENODO_PRODUCTION

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
