from jupyter_server.base.handlers import APIHandler

from inveniordm_auth.token_store import BoundedTokenStore, FileTokenStore, StoredToken
from inveniordm_auth.remote_servers import RemoteServerId, RemoteServerRegistry

from ..inveniordm_auth.auth_controller import InvenioRDMAuthController
from ..inveniordm_auth.local_auth_controller import LocalInvenioRDMAuthController
from .inveniordm_requests import InvenioRDMRequests
from .inveniordm_requests_factory import (
    InvenioRDMRequestsFactory,
    get_remote_server_override,
)


class LocalInvenioRDMRequestsFactory(InvenioRDMRequestsFactory):
    def __init__(self, remote_servers: RemoteServerRegistry):
        super().__init__(remote_servers)
        self.token_store = BoundedTokenStore(FileTokenStore())
        self._auth_controller = LocalInvenioRDMAuthController(
            self.token_store,
            remote_servers,
        )

    @property
    def auth_controller(self) -> InvenioRDMAuthController:
        return self._auth_controller

    def create_inveniordm_requests(self, handler: APIHandler) -> InvenioRDMRequests:
        remote_server_override = get_remote_server_override(handler)
        token = self.token_store.get_token()

        if remote_server_override is not None:
            headers = self._headers_for_token(token, remote_server_override)
            return InvenioRDMRequests(
                url=self.remote_servers.get(remote_server_override).base_url,
                headers=headers,
                inveniordm_user_id=(
                    token.inveniordm_user_id if token is not None and headers else None
                ),
            )

        if token is not None:
            return InvenioRDMRequests(
                url=self.remote_servers.get(token.remote_server_id).base_url,
                headers=self._headers_for_token(token, token.remote_server_id),
                inveniordm_user_id=token.inveniordm_user_id,
            )

        return InvenioRDMRequests(url=self.remote_servers.default.base_url)

    def _headers_for_token(
        self,
        token: StoredToken | None,
        remote_server_id: RemoteServerId,
    ) -> dict[str, str]:
        if token is None or token.remote_server_id != remote_server_id:
            return {}

        return {"Authorization": f"Bearer {token.access_token}"}
