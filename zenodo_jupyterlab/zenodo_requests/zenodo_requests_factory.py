import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from jupyter_core.paths import jupyter_data_dir
from jupyter_server.base.handlers import APIHandler

from .token_store import FileTokenStore
from .zenodo import is_zenodo_request_authenticated
from .zenodo_requests import AccessTokenStatus, ZenodoRequests

if TYPE_CHECKING:
    from .local_zenodo_requests_factory import LocalZenodoRequestsFactory
    from .proxy_zenodo_requests_factory import ProxyZenodoRequestsFactory


def default_token_store_path() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "tokens.json"


def get_user_token_id(handler: APIHandler) -> str:
    """
    Get a unique ID for the current user to associate with their access token.
    """
    return handler.current_user.username


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


def __getattr__(name: str):
    if name == "LocalZenodoRequestsFactory":
        from .local_zenodo_requests_factory import LocalZenodoRequestsFactory

        return LocalZenodoRequestsFactory
    if name == "ProxyZenodoRequestsFactory":
        from .proxy_zenodo_requests_factory import ProxyZenodoRequestsFactory

        return ProxyZenodoRequestsFactory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def create_zenodo_requests_factory(
    factory_type: str = "proxy",
) -> ZenodoRequestsFactory:
    if factory_type == "local":
        from .local_zenodo_requests_factory import LocalZenodoRequestsFactory

        return LocalZenodoRequestsFactory(
            FileTokenStore(
                os.environ.get(
                    "ZENODO_JUPYTERLAB_TOKEN_STORE",
                    str(default_token_store_path()),
                )
            )
        )
    if factory_type == "proxy":
        from .proxy_zenodo_requests_factory import ProxyZenodoRequestsFactory

        return ProxyZenodoRequestsFactory()

    raise ValueError(
        "ZENODO_JUPYTERLAB_REQUESTS_FACTORY must be either 'proxy' or 'local'"
    )
