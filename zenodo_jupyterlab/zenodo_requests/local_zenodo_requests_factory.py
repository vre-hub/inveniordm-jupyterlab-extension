from jupyter_server.base.handlers import APIHandler

from zenodo_auth.token_store import BoundedTokenStore, FileTokenStore, StoredToken
from zenodo_auth.remote_servers import (
    RemoteServerId,
    get_remote_server,
)

from ..zenodo_auth.auth_controller import ZenodoAuthController
from ..zenodo_auth.local_auth_controller import LocalZenodoAuthController
from .zenodo_requests import ZenodoRequests
from .zenodo_requests_factory import (
    ZenodoRequestsFactory,
    get_remote_server_override,
)


class LocalZenodoRequestsFactory(ZenodoRequestsFactory):
    def __init__(self):
        self.token_store = BoundedTokenStore(FileTokenStore())
        self._auth_controller = LocalZenodoAuthController(self.token_store)

    @property
    def auth_controller(self) -> ZenodoAuthController:
        return self._auth_controller

    def create_zenodo_requests(self, handler: APIHandler) -> ZenodoRequests:
        remote_server_override = get_remote_server_override(handler)
        token = self.token_store.get_token()

        if remote_server_override is not None:
            headers = self._headers_for_token(token, remote_server_override)
            return ZenodoRequests(
                url=get_remote_server(remote_server_override).base_url,
                headers=headers,
                zenodo_user_id=(
                    token.zenodo_user_id if token is not None and headers else None
                ),
            )

        if token is not None:
            return ZenodoRequests(
                url=get_remote_server(token.remote_server_id).base_url,
                headers=self._headers_for_token(token, token.remote_server_id),
                zenodo_user_id=token.zenodo_user_id,
            )

        return ZenodoRequests(
            url=get_remote_server(RemoteServerId.ZENODO_PRODUCTION).base_url
        )

    def _headers_for_token(
        self,
        token: StoredToken | None,
        remote_server_id: RemoteServerId,
    ) -> dict[str, str]:
        if token is None or token.remote_server_id != remote_server_id:
            return {}

        return {"Authorization": f"Bearer {token.access_token}"}
