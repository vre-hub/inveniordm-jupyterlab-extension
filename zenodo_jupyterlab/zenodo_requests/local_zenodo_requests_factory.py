import json
import os
from urllib.parse import urlparse

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from tornado.web import RequestHandler

from zenodo_auth.auth_service import OAuthCallback, ZenodoAuthService
from zenodo_auth.token_store import BoundedTokenStore, FileTokenStore, StoredToken
from zenodo_auth.tornado_oauth import (
    begin_zenodo_oauth_login,
    finish_zenodo_oauth_callback,
)
from .zenodo_requests import ZenodoRequests
from .zenodo_requests_factory import (
    ZenodoRequestsFactory,
    get_sandbox_override,
)

SANDBOX_OAUTH_CLIENT_ID="ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU"
PRODUCTION_OAUTH_CLIENT_ID="HaWBPRb7lsif7cqTypUNeFni9PJOoTm5IcjTJrtt"
OAUTH_SCOPE="deposit:write deposit:actions"

class LocalZenodoRequestsFactory(ZenodoRequestsFactory):
    production_url = "https://zenodo.org"
    sandbox_url = "https://sandbox.zenodo.org"

    def __init__(self):
        self.token_store = BoundedTokenStore(FileTokenStore())

        # key: (sandbox, redirect_uri), value: ZenodoAuthService
        # e.g. (True, "https://swan.cern.ch/zenodo-jupyterlab/auth/callback") -> ZenodoAuthService
        self.auth_services: dict[tuple[bool, str], ZenodoAuthService] = {}

    def create_zenodo_requests(self, handler: APIHandler) -> ZenodoRequests:
        sandbox_override = get_sandbox_override(handler)
        token = self.token_store.get_token()

        if sandbox_override is not None:
            headers = self._headers_for_token(token, sandbox_override)
            return ZenodoRequests(
                url=self._server_url(sandbox_override),
                headers=headers,
            )

        if token is not None:
            return ZenodoRequests(
                url=self._server_url(token.sandbox),
                headers=self._headers_for_token(token, token.sandbox),
            )

        return ZenodoRequests(url=self.production_url)

    def is_sandbox(self, zenodo_requests: ZenodoRequests) -> bool:
        return zenodo_requests.url == self.sandbox_url

    def handle_auth(self, handler: APIHandler, action: str) -> None:
        if action == "login":
            sandbox = self._oauth_sandbox(handler)
            begin_zenodo_oauth_login(
                handler,
                auth_service=self._auth_service(handler, sandbox),
                default_return_to=self._default_return_to(handler),
                is_allowed_return_to=lambda return_to: self._is_allowed_return_to(
                    handler,
                    return_to,
                ),
            )
            return

        if action == "logout":
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
            return

        if action == "callback":
            auth_service = self._auth_service_for_callback(handler)
            finish_zenodo_oauth_callback(
                handler,
                auth_service=auth_service,
                on_success=lambda callback_handler, callback: (
                    self._complete_oauth_login(
                        callback_handler,
                        callback,
                        sandbox=auth_service.sandbox,
                    )
                ),
            )
            return

        handler.set_status(404)
        handler.finish(json.dumps({"message": "Unknown auth action"}))

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

    def _headers_for_token(
        self,
        token: StoredToken | None,
        sandbox: bool,
    ) -> dict[str, str]:
        if token is None or token.sandbox != sandbox:
            return {}

        return {"Authorization": f"Bearer {token.access_token}"}

    def _server_url(self, sandbox: bool) -> str:
        return self.sandbox_url if sandbox else self.production_url

    def _auth_service(self, handler: APIHandler, sandbox: bool) -> ZenodoAuthService:
        redirect_uri = self._oauth_callback_url(handler)
        key = (sandbox, redirect_uri)
        client_id = SANDBOX_OAUTH_CLIENT_ID if sandbox else PRODUCTION_OAUTH_CLIENT_ID
        if key not in self.auth_services:
            self.auth_services[key] = ZenodoAuthService(
                zenodo_base_url=self._server_url(sandbox),
                client_id=client_id,
                redirect_uri=redirect_uri,
                scope=OAUTH_SCOPE,
                sandbox=sandbox,
            )
        return self.auth_services[key]

    def _auth_service_for_callback(self, handler: APIHandler) -> ZenodoAuthService:
        state = handler.get_query_argument("state", None)
        for auth_service in self.auth_services.values():
            if state in auth_service.oauth_states:
                return auth_service

        return self._auth_service(handler, self._oauth_sandbox(handler))

    def _oauth_sandbox(self, handler: APIHandler) -> bool:
        sandbox_override = get_sandbox_override(handler)
        return sandbox_override if sandbox_override is not None else False

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
