from inveniordm_auth.remote_servers import RemoteServerRegistry

from .local_inveniordm_requests_factory import LocalInvenioRDMRequestsFactory
from .proxy_inveniordm_requests_factory import ProxyInvenioRDMRequestsFactory
from .inveniordm_requests_factory import InvenioRDMRequestsFactory


def create_inveniordm_requests_factory(
    remote_servers: RemoteServerRegistry,
    factory_type: str = "proxy",
) -> InvenioRDMRequestsFactory:
    if factory_type == "local":
        return LocalInvenioRDMRequestsFactory(remote_servers)
    if factory_type == "proxy":
        return ProxyInvenioRDMRequestsFactory(remote_servers)

    raise ValueError(
        "INVENIORDM_JUPYTERLAB_REQUESTS_FACTORY must be either 'proxy' or 'local'"
    )
