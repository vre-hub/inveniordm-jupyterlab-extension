from collections.abc import Mapping
from typing import Any

from traitlets import Bool, Dict, Enum, Unicode
from traitlets.config import Configurable

from inveniordm_auth.remote_servers import RemoteServerRegistry

DEFAULT_REMOTE_SERVERS: dict[str, dict[str, str]] = {
    "zenodo": {
        "label": "Zenodo",
        "base_url": "https://zenodo.org",
    },
    "cds": {
        "label": "CDS",
        "base_url": "https://repository.cern",
    },
}

BUILTIN_LOCAL_OAUTH_CLIENT_IDS = {
    "zenodo": "5LkeWfl5Yvhiz42JkAYQI64UYAsyxll2opUsNdmN",
    "cds": "BUh7Vh0IjlEbB25GIhgj2fWxKxWce824f32lpcTf",
}

remote_servers_modes = ["extend", "replace", "prepend"]
request_modes = ["local", "proxy"]


def _extend_remote_servers(
    remote_servers: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    # built-ins first; overrides merge in place; new servers append.
    configured_servers: dict[str, dict[str, Any]] = {
        server_id: dict(settings)
        for server_id, settings in DEFAULT_REMOTE_SERVERS.items()
    }
    for server_id, settings in remote_servers.items():
        configured_servers[server_id] = {
            **configured_servers.get(server_id, {}),
            **settings,
        }
    return configured_servers


def _prepend_remote_servers(
    remote_servers: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    # configured servers first; matching built-ins supply missing fields; untouched built-ins follow.
    configured_servers: dict[str, dict[str, Any]] = {
        server_id: {
            **DEFAULT_REMOTE_SERVERS.get(server_id, {}),
            **settings,
        }
        for server_id, settings in remote_servers.items()
    }
    for server_id, settings in DEFAULT_REMOTE_SERVERS.items():
        configured_servers.setdefault(server_id, dict(settings))
    return configured_servers


def _replace_remote_servers(
    remote_servers: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    # only configured IDs are included, but matching built-ins still supply missing fields.
    return {
        server_id: {
            **DEFAULT_REMOTE_SERVERS.get(server_id, {}),
            **settings,
        }
        for server_id, settings in remote_servers.items()
    }


class InvenioRDMJupyterLab(Configurable):
    enable_builtin_local_oauth = Bool(
        default_value=True,
        config=True,
        help="Use the built-in OAuth client IDs for supported remote servers.",
    )

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
        help=(
            "Which configured and built-in remote servers to include, and in what "
            "order. Configured fields override built-in fields for matching IDs."
        ),
    )

    remote_servers = Dict(
        key_trait=None,
        value_trait=Dict(),
        default_value=DEFAULT_REMOTE_SERVERS,
        config=True,
        help=(
            "Remote InvenioRDM server definitions keyed by ID. Definitions for "
            "built-in IDs may contain only the fields to override or add."
        ),
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
            configured_servers = _extend_remote_servers(self.remote_servers)
        elif self.remote_servers_mode == "prepend":
            configured_servers = _prepend_remote_servers(self.remote_servers)
        else:
            configured_servers = _replace_remote_servers(self.remote_servers)

        if self.enable_builtin_local_oauth:
            for server_id, oauth_client_id in BUILTIN_LOCAL_OAUTH_CLIENT_IDS.items():
                if server_id in configured_servers:
                    configured_servers[server_id].setdefault(
                        "oauth_client_id", oauth_client_id
                    )

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
