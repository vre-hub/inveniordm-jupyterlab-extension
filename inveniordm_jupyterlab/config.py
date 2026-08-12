from typing import Any

from traitlets import Dict, Enum, Unicode
from traitlets.config import Configurable

from inveniordm_auth.remote_servers import RemoteServerRegistry

DEFAULT_REMOTE_SERVERS: dict[str, dict[str, str]] = {
    "zenodo_production": {
        "label": "Zenodo",
        "base_url": "https://zenodo.org",
    },
    "cds_repository": {
        "label": "CDS",
        "base_url": "https://repository.cern",
    },
}

remote_servers_modes = ["extend", "replace", "prepend"]
request_modes = ["local", "proxy"]


class InvenioRDMJupyterLab(Configurable):
    request_mode = Enum(
        request_modes,
        default_value="local",
        config=True,
        help="Mode used for InvenioRDM API requests.",
    )

    remote_servers_mode = Enum(
        remote_servers_modes,
        default_value="replace",
        config=True,
        help="How configured remote servers should be applied to the built-in defaults.",
    )

    remote_servers = Dict(
        key_trait=None,
        value_trait=Dict(),
        default_value=DEFAULT_REMOTE_SERVERS,
        config=True,
        help="Remote InvenioRDM servers available to the extension, keyed by ID.",
    )

    default_remote_server = Unicode(
        default_value="",
        allow_none=True,
        config=True,
        help=(
            "ID of the default remote server to use when no override is provided. "
            "If not set, the first configured server is used."
        ),
    )

    def remote_server_registry(self) -> RemoteServerRegistry:
        if self.remote_servers_mode == "extend":
            configured_servers: dict[str, dict[str, Any]] = {
                **DEFAULT_REMOTE_SERVERS,
                **self.remote_servers,
            }
        elif self.remote_servers_mode == "prepend":
            configured_servers = {
                **self.remote_servers,
                **DEFAULT_REMOTE_SERVERS,
            }
        else:
            configured_servers = dict(self.remote_servers)

        default_remote_server_id = (
            self.default_remote_server.strip()
            if self.default_remote_server is not None
            else None
        )
        if default_remote_server_id == "":
            default_remote_server_id = None

        registry = RemoteServerRegistry(
            configured_servers,
            default_server_id=default_remote_server_id,
        )
        if self.request_mode == "proxy":
            registry.validate_proxy_configuration()
        return registry
