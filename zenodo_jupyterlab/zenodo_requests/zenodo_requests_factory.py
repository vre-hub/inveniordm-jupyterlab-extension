from abc import ABC, abstractmethod

from jupyter_server.base.handlers import APIHandler

from zenodo_auth.remote_servers import RemoteServerId, RemoteServerRegistry

from ..zenodo_auth.auth_controller import ZenodoAuthController
from .zenodo import check_zenodo_authentication
from .zenodo_requests import AccessTokenStatus, ZenodoRequests


def get_remote_server_override(handler: APIHandler) -> RemoteServerId | None:
    remote_server = handler.get_query_argument("remote_server", None)
    if remote_server is None:
        return None
    return remote_server


class ZenodoRequestsFactory(ABC):
    def __init__(self, remote_servers: RemoteServerRegistry):
        self.remote_servers = remote_servers

    @property
    @abstractmethod
    def auth_controller(self) -> ZenodoAuthController:
        pass

    @abstractmethod
    def create_zenodo_requests(self, handler: APIHandler) -> ZenodoRequests:
        pass

    def get_remote_server_id(self, zenodo_requests: ZenodoRequests) -> RemoteServerId:
        return self.remote_servers.by_url(zenodo_requests.url).id

    def get_access_token_status(self, handler: APIHandler) -> AccessTokenStatus:
        zenodo_requests = self.create_zenodo_requests(handler)
        authentication_present = bool(zenodo_requests.headers)
        remote_server_id = self.get_remote_server_id(zenodo_requests)
        return AccessTokenStatus(
            access_token_present=authentication_present,
            access_token_valid=(
                check_zenodo_authentication(
                    base_url=zenodo_requests.url,
                    headers=zenodo_requests.headers,
                )
                if authentication_present
                else False
            ),
            remote_server_id=remote_server_id,
            remote_server_label=self.remote_servers.get(remote_server_id).label,
            remote_server_base_url=self.remote_servers.get(remote_server_id).base_url,
        )
