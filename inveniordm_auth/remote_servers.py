from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeAlias

RemoteServerId: TypeAlias = str


class UnknownRemoteServerError(LookupError):
    def __init__(self, remote_server_id: RemoteServerId):
        self.remote_server_id = remote_server_id
        super().__init__(remote_server_id)

    def __str__(self) -> str:
        return f"Unknown remote server: {self.remote_server_id}"


@dataclass(frozen=True)
class RemoteServer:
    id: RemoteServerId
    label: str
    base_url: str
    oauth_client_id: str
    proxy_url: str
    proxy_session_cookie_name: str


class RemoteServerRegistry:
    """The remote servers made available by the Jupyter server configuration."""

    def __init__(
        self,
        configured_servers: Mapping[str, Mapping[str, Any]],
        default_server_id: str | None = None,
    ):
        self._servers: dict[str, RemoteServer] = {}
        for server_id, settings in configured_servers.items():
            if not isinstance(server_id, str) or not server_id.strip():
                raise ValueError("Remote server IDs must be non-empty strings")
            normalized_id = server_id.strip()
            self._servers[normalized_id] = self._from_config(normalized_id, settings)
        if not self._servers:
            raise ValueError("InvenioRDMJupyterLab.remote_servers must not be empty")

        if default_server_id is not None:
            if not isinstance(default_server_id, str) or not default_server_id.strip():
                raise ValueError("Default remote server ID must be a non-empty string")
            normalized_default_server_id = default_server_id.strip()
            if normalized_default_server_id not in self._servers:
                raise ValueError(
                    f"Unknown default remote server ID: {normalized_default_server_id}"
                )
            self._default_server_id = normalized_default_server_id
        else:
            self._default_server_id = None

    @staticmethod
    def _from_config(
        server_id: str,
        settings: Mapping[str, Any],
    ) -> RemoteServer:
        required_fields = [
            "label",
            "base_url",
            "oauth_client_id",
        ]
        values: dict[str, str] = {}
        for field in required_fields:
            value = settings.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Remote server {server_id!r} requires a non-empty {field!r}"
                )
            values[field] = value.strip()

        for field in ("proxy_url", "proxy_session_cookie_name"):
            value = settings.get(field, "")
            if not isinstance(value, str):
                raise ValueError(
                    f"Remote server {server_id!r} requires {field!r} to be a string"
                )
            values[field] = value.strip()

        return RemoteServer(
            id=server_id,
            label=values["label"],
            base_url=values["base_url"].rstrip("/"),
            oauth_client_id=values["oauth_client_id"],
            proxy_url=values["proxy_url"].rstrip("/"),
            proxy_session_cookie_name=values["proxy_session_cookie_name"],
        )

    @property
    def default(self) -> RemoteServer:
        if self._default_server_id is not None:
            return self.get(self._default_server_id)
        return next(iter(self._servers.values()))

    def get(self, server_id: RemoteServerId) -> RemoteServer:
        try:
            return self._servers[server_id]
        except KeyError as error:
            raise UnknownRemoteServerError(server_id) from error

    def all(self) -> tuple[RemoteServer, ...]:
        return tuple(self._servers.values())

    def validate_proxy_configuration(self) -> None:
        for server in self._servers.values():
            for field in ("proxy_url", "proxy_session_cookie_name"):
                if not getattr(server, field):
                    raise ValueError(
                        f"Remote server {server.id!r} requires a non-empty {field!r} "
                        "in proxy request mode"
                    )

    def by_url(self, url: str) -> RemoteServer:
        normalized_url = url.rstrip("/")
        for server in self._servers.values():
            known_urls = {server.base_url}
            if server.proxy_url:
                known_urls.add(server.proxy_url)
            if normalized_url in known_urls:
                return server
        raise ValueError(f"Unknown remote server URL: {url}")
