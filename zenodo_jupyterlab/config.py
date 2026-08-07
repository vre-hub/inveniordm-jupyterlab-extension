from typing import Any

from traitlets import Dict
from traitlets.config import Configurable

from zenodo_auth.remote_servers import RemoteServerRegistry


class ZenodoJupyterLab(Configurable):
    remote_servers = Dict(
        key_trait=None,
        value_trait=Dict(),
        default_value={},
        config=True,
        help="Remote InvenioRDM servers available to the extension, keyed by ID.",
    )

    def remote_server_registry(self) -> RemoteServerRegistry:
        configured_servers: dict[str, dict[str, Any]] = self.remote_servers
        return RemoteServerRegistry(configured_servers)
