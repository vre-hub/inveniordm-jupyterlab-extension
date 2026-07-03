from jupyter_server.base.handlers import APIHandler

from zenodo_auth.token_store import BoundedTokenStore, FileTokenStore, StoredToken
from ..zenodo_auth.auth_controller import ZenodoAuthController
from ..zenodo_auth.local_auth_controller import LocalZenodoAuthController
from .zenodo_requests import ZenodoRequests
from .zenodo_requests_factory import (
    ZenodoRequestsFactory,
    get_sandbox_override,
)


class LocalZenodoRequestsFactory(ZenodoRequestsFactory):
    production_url = "https://zenodo.org"
    sandbox_url = "https://sandbox.zenodo.org"

    def __init__(self):
        self.token_store = BoundedTokenStore(FileTokenStore())
        self._auth_controller = LocalZenodoAuthController(self.token_store)

    @property
    def auth_controller(self) -> ZenodoAuthController:
        return self._auth_controller

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
