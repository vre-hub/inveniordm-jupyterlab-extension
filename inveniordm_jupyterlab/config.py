from typing import Any

from traitlets import Dict, Enum, Unicode
from traitlets.config import Configurable

from inveniordm_auth.remote_servers import RemoteServerRegistry

# The default OAuth client IDs work if jupyterlab is http://localhost:8888 or http://127.0.0.1:8888
# TODO replace the oauth ids again once the oauth applications are created from a service account
DEFAULT_REMOTE_SERVERS: dict[str, dict[str, str]] = {
    "zenodo_production": {
        "label": "Zenodo",
        "base_url": "https://zenodo.org",
        "oauth_client_id": "5LkeWfl5Yvhiz42JkAYQI64UYAsyxll2opUsNdmN",
    },
    "cds_repository": {
        "oauth_client_id": "BUh7Vh0IjlEbB25GIhgj2fWxKxWce824f32lpcTf",
        "label": "CDS",
        "base_url": "https://repository.cern",
    },
}

request_modes = ["local", "proxy"]


class InvenioRDMJupyterLab(Configurable):
    request_mode = Enum(
        request_modes,
        default_value="local",
        config=True,
        help="Mode used for InvenioRDM API requests.",
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
        if self.remote_servers is None:
            configured_servers: dict[str, dict[str, Any]] = DEFAULT_REMOTE_SERVERS
        else:
            configured_servers = self.remote_servers

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
