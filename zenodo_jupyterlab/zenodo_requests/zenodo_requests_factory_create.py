from zenodo_auth.remote_servers import RemoteServerRegistry

from .local_zenodo_requests_factory import LocalZenodoRequestsFactory
from .proxy_zenodo_requests_factory import ProxyZenodoRequestsFactory
from .zenodo_requests_factory import ZenodoRequestsFactory


def create_zenodo_requests_factory(
    remote_servers: RemoteServerRegistry,
    factory_type: str = "proxy",
) -> ZenodoRequestsFactory:
    if factory_type == "local":
        return LocalZenodoRequestsFactory(remote_servers)
    if factory_type == "proxy":
        return ProxyZenodoRequestsFactory(remote_servers)

    raise ValueError(
        "ZENODO_JUPYTERLAB_REQUESTS_FACTORY must be either 'proxy' or 'local'"
    )
