from typing import Any

from traitlets import Dict, Enum, Unicode
from traitlets.config import Configurable

from zenodo_auth.remote_servers import RemoteServerRegistry

DEFAULT_REMOTE_SERVERS: dict[str, dict[str, str]] = {
    "zenodo_production": {
        "label": "Production",
        "base_url": "https://zenodo.org",
        "oauth_client_id": "HaWBPRb7lsif7cqTypUNeFni9PJOoTm5IcjTJrtt",
        "proxy_url": "http://127.0.0.1:8003",
        "proxy_session_cookie_name": "zenodo_production_proxy_session",
    },
    "zenodo_sandbox": {
        "label": "Sandbox",
        "base_url": "https://sandbox.zenodo.org",
        "oauth_client_id": "ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU",
        "proxy_url": "http://127.0.0.1:8001",
        "proxy_session_cookie_name": "zenodo_sandbox_proxy_session",
    },
    "cds_repository": {
        "label": "CDS",
        "base_url": "https://repository.cern",
        "oauth_client_id": "q4szrkotZqAuRA6HhGeajJsqTqEd6t6lTHHGLWD4",
        "proxy_url": "http://127.0.0.1:8004",
        "proxy_session_cookie_name": "cds_repository_proxy_session",
    },
    "cds_repository_sandbox": {
        "label": "CDS Sandbox",
        "base_url": "https://sandbox-cds-rdm.web.cern.ch",
        "oauth_client_id": "J5nzeas8LpcGllJysNJzj52YT0qpvJbVA0AN0F5y",
        "proxy_url": "http://127.0.0.1:8005",
        "proxy_session_cookie_name": "cds_repository_sandbox_proxy_session",
    },
}

remote_servers_modes = ["extend", "replace"]


class ZenodoJupyterLab(Configurable):
    remote_servers_mode = Enum(
        remote_servers_modes,
        default_value="extend",
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
        if self.remote_servers_mode not in remote_servers_modes:
            raise ValueError(
                f"Invalid remote_servers_mode: {self.remote_servers_mode}. "
                f"Must be one of {remote_servers_modes}."
            )
        if self.remote_servers_mode == "extend":
            configured_servers: dict[str, dict[str, Any]] = {
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

        return RemoteServerRegistry(
            configured_servers,
            default_server_id=default_remote_server_id,
        )
