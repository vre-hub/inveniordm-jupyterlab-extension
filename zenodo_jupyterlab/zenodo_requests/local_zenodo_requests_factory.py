import json

from jupyter_server.base.handlers import APIHandler

from zenodo_auth.token_store import BoundedTokenStore, FileTokenStore, StoredToken
from .zenodo import is_zenodo_request_authenticated
from .zenodo_requests import AccessTokenStatus, ZenodoRequests
from .zenodo_requests_factory import (
    ZenodoRequestsFactory,
    get_sandbox_override,
)


class LocalZenodoRequestsFactory(ZenodoRequestsFactory):
    production_url = "https://zenodo.org"
    sandbox_url = "https://sandbox.zenodo.org"

    def __init__(self):
        self.token_store = BoundedTokenStore(FileTokenStore())

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

    def put_access_token(self, handler: APIHandler) -> None:
        data = handler.get_json_body() or {}
        access_token = data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            handler.set_status(400)
            handler.finish(json.dumps({"message": "Missing access_token"}))
            return

        headers = {"Authorization": f"Bearer {access_token}"}
        sandbox = self._check_if_token_is_sandbox(headers=headers)
        self.token_store.set_token(
            access_token,
            True,
            sandbox=sandbox,
        )
        handler.finish(
            json.dumps(
                AccessTokenStatus(
                    access_token_present=True,
                    access_token_valid=True,
                    sandbox=sandbox,
                ).__dict__
            )
        )

    def delete_access_token(self, handler: APIHandler) -> None:
        self.token_store.remove_token()
        handler.finish(json.dumps({"message": "Zenodo access token removed"}))

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

    def _check_if_token_is_sandbox(
        self,
        *,
        headers: dict[str, str],
    ) -> bool:
        sandbox = is_zenodo_request_authenticated(
            base_url=self.sandbox_url,
            headers=headers,
        )
        if sandbox:
            return True
        prod = is_zenodo_request_authenticated(
            base_url=self.production_url,
            headers=headers,
        )
        if prod:
            return False
        raise ValueError("Access token is not valid")
