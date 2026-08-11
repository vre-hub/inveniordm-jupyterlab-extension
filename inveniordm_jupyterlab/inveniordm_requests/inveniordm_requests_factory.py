from abc import ABC, abstractmethod

from jupyter_server.base.handlers import APIHandler

from inveniordm_auth.remote_servers import RemoteServerId, RemoteServerRegistry

from ..inveniordm_auth.auth_controller import InvenioRDMAuthController
from .inveniordm import check_inveniordm_authentication
from .inveniordm_requests import AccessTokenStatus, InvenioRDMRequests


def get_remote_server_override(handler: APIHandler) -> RemoteServerId | None:
    remote_server = handler.get_query_argument("remote_server", None)
    if remote_server is None:
        return None
    return remote_server


class InvenioRDMRequestsFactory(ABC):
    def __init__(self, remote_servers: RemoteServerRegistry):
        self.remote_servers = remote_servers

    @property
    @abstractmethod
    def auth_controller(self) -> InvenioRDMAuthController:
        pass

    @abstractmethod
    def create_inveniordm_requests(self, handler: APIHandler) -> InvenioRDMRequests:
        pass

    def get_remote_server_id(
        self, inveniordm_requests: InvenioRDMRequests
    ) -> RemoteServerId:
        return self.remote_servers.by_url(inveniordm_requests.url).id

    def get_access_token_status(self, handler: APIHandler) -> AccessTokenStatus:
        inveniordm_requests = self.create_inveniordm_requests(handler)
        authentication_present = bool(inveniordm_requests.headers)
        remote_server_id = self.get_remote_server_id(inveniordm_requests)
        return AccessTokenStatus(
            access_token_present=authentication_present,
            access_token_valid=(
                check_inveniordm_authentication(
                    base_url=inveniordm_requests.url,
                    headers=inveniordm_requests.headers,
                )
                if authentication_present
                else False
            ),
            remote_server_id=remote_server_id,
            remote_server_label=self.remote_servers.get(remote_server_id).label,
            remote_server_base_url=self.remote_servers.get(remote_server_id).base_url,
        )
