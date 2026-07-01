from abc import ABC, abstractmethod

from jupyter_server.base.handlers import APIHandler

from .zenodo import is_zenodo_request_authenticated
from .zenodo_requests import AccessTokenStatus, ZenodoRequests


def get_sandbox_override(handler: APIHandler) -> bool | None:
    if handler.get_query_argument("sandbox", None) is None:
        return None

    return handler.get_query_argument("sandbox", "false").lower() in ("1", "true")


class ZenodoRequestsFactory(ABC):
    @abstractmethod
    def create_zenodo_requests(self, handler: APIHandler) -> ZenodoRequests:
        pass

    @abstractmethod
    def is_sandbox(self, zenodo_requests: ZenodoRequests) -> bool:
        """
        Check if the given ZenodoRequests instance is for the sandbox server.
        """
        pass

    def get_access_token_status(self, handler: APIHandler) -> AccessTokenStatus:
        zenodo_requests = self.create_zenodo_requests(handler)
        authentication_present = bool(zenodo_requests.headers)
        return AccessTokenStatus(
            access_token_present=authentication_present,
            access_token_valid=(
                is_zenodo_request_authenticated(
                    base_url=zenodo_requests.url,
                    headers=zenodo_requests.headers,
                )
                if authentication_present
                else False
            ),
            sandbox=self.is_sandbox(zenodo_requests),
        )

    def handle_auth(self, handler: APIHandler, action: str) -> None:
        raise NotImplementedError("OAuth proxy authentication is not configured")

    def put_access_token(self, handler: APIHandler) -> None:
        raise NotImplementedError("Manual Zenodo access tokens are not configured")

    def delete_access_token(self, handler: APIHandler) -> None:
        raise NotImplementedError("Manual Zenodo access tokens are not configured")
