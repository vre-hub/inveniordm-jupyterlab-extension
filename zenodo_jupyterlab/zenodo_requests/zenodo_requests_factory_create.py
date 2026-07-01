from .local_zenodo_requests_factory import LocalZenodoRequestsFactory
from .proxy_zenodo_requests_factory import ProxyZenodoRequestsFactory
from .zenodo_requests_factory import ZenodoRequestsFactory


def create_zenodo_requests_factory(
    factory_type: str = "proxy",
) -> ZenodoRequestsFactory:
    if factory_type == "local":
        return LocalZenodoRequestsFactory()
    if factory_type == "proxy":
        return ProxyZenodoRequestsFactory()

    raise ValueError(
        "ZENODO_JUPYTERLAB_REQUESTS_FACTORY must be either 'proxy' or 'local'"
    )
