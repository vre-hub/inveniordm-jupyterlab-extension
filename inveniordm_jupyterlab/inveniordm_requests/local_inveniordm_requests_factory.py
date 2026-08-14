from jupyter_server.base.handlers import APIHandler

from inveniordm_auth.token_store import FileTokenStore, StoredToken
from inveniordm_auth.remote_servers import RemoteServerId, RemoteServerRegistry

from ..inveniordm_auth.auth_controller import InvenioRDMAuthController
from ..inveniordm_auth.local_auth_controller import LocalInvenioRDMAuthController
from .inveniordm_requests import InvenioRDMRequests
from .inveniordm_requests_factory import (
    InvenioRDMRequestsFactory,
    get_remote_server_override,
)


class LocalInvenioRDMRequestsFactory(InvenioRDMRequestsFactory):
    """Create API clients authenticated from the local token store."""
    def __init__(self, remote_servers: RemoteServerRegistry):
        """Initialize local token storage and OAuth handling."""
        super().__init__(remote_servers)
        self.token_store = FileTokenStore()
        self._auth_controller = LocalInvenioRDMAuthController(
            self.token_store,
            remote_servers,
        )

    @property
    def auth_controller(self) -> InvenioRDMAuthController:
        """Return the local OAuth controller."""
        return self._auth_controller

    def create_inveniordm_requests(self, handler: APIHandler) -> InvenioRDMRequests:
        """Create a client for the requested or default remote server."""
        remote_server_id = (
            get_remote_server_override(handler) or self.remote_servers.default.id
        )
        server = self.remote_servers.get(remote_server_id)
        token = self.token_store.get_token(remote_server_id)
        headers = self._headers_for_token(token, remote_server_id)

        return InvenioRDMRequests(
            url=server.base_url,
            headers=headers,
            inveniordm_user_id=(
                token.inveniordm_user_id if token is not None and headers else None
            ),
        )

    def _headers_for_token(
        self,
        token: StoredToken | None,
        remote_server_id: RemoteServerId,
    ) -> dict[str, str]:
        """Build authorization headers when the token matches the server."""
        if token is None or token.remote_server_id != remote_server_id:
            return {}

        return {"Authorization": f"Bearer {token.access_token}"}
