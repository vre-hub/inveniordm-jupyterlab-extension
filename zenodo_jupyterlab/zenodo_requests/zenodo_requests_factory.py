from abc import ABC, abstractmethod

from jupyter_server.base.handlers import APIHandler

from zenodo_auth.remote_servers import RemoteServerId, get_remote_server_by_url

from ..zenodo_auth.auth_controller import ZenodoAuthController
from .zenodo import check_zenodo_authentication
from .zenodo_requests import AccessTokenStatus, ZenodoRequests


def get_remote_server_override(handler: APIHandler) -> RemoteServerId | None:
    remote_server = handler.get_query_argument("remote_server", None)
    if remote_server is None:
        return None
    return RemoteServerId(remote_server)


class ZenodoRequestsFactory(ABC):
    @property
    @abstractmethod
    def auth_controller(self) -> ZenodoAuthController:
        pass

    @abstractmethod
    def create_zenodo_requests(self, handler: APIHandler) -> ZenodoRequests:
        pass

    def get_remote_server_id(self, zenodo_requests: ZenodoRequests) -> RemoteServerId:
        return get_remote_server_by_url(zenodo_requests.url).id

    def get_access_token_status(self, handler: APIHandler) -> AccessTokenStatus:
        zenodo_requests = self.create_zenodo_requests(handler)
        authentication_present = bool(zenodo_requests.headers)
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
            remote_server_id=self.get_remote_server_id(zenodo_requests),
        )
