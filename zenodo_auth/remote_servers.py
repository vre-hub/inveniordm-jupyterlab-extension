import os
from dataclasses import dataclass
from enum import StrEnum


class RemoteServerId(StrEnum):
    ZENODO_PRODUCTION = "zenodo_production"
    ZENODO_SANDBOX = "zenodo_sandbox"
    CDS_REPOSITORY = "cds_repository"
    CDS_REPOSITORY_SANDBOX = "cds_repository_sandbox"
    INVENIORDM_LOCAL = "inveniordm_local"


@dataclass(frozen=True)
class RemoteServer:
    id: RemoteServerId
    label: str
    base_url: str
    oauth_client_id: str
    proxy_url: str
    proxy_session_cookie_name: str


_REMOTE_SERVERS = {
    RemoteServerId.ZENODO_PRODUCTION: RemoteServer(
        id=RemoteServerId.ZENODO_PRODUCTION,
        label="Production",
        base_url="https://zenodo.org",
        oauth_client_id="HaWBPRb7lsif7cqTypUNeFni9PJOoTm5IcjTJrtt",
        proxy_url="http://127.0.0.1:8003",
        proxy_session_cookie_name=os.environ.get(
            "ZENODO_PRODUCTION_PROXY_SESSION_COOKIE_NAME",
            "zenodo_production_proxy_session",
        ),
    ),
    RemoteServerId.ZENODO_SANDBOX: RemoteServer(
        id=RemoteServerId.ZENODO_SANDBOX,
        label="Sandbox",
        base_url="https://sandbox.zenodo.org",
        oauth_client_id="ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU",
        proxy_url="http://127.0.0.1:8001",
        proxy_session_cookie_name=os.environ.get(
            "ZENODO_SANDBOX_PROXY_SESSION_COOKIE_NAME",
            "zenodo_sandbox_proxy_session",
        ),
    ),
    RemoteServerId.CDS_REPOSITORY: RemoteServer(
        id=RemoteServerId.CDS_REPOSITORY,
        label="CDS",
        base_url="https://repository.cern",
        oauth_client_id="q4szrkotZqAuRA6HhGeajJsqTqEd6t6lTHHGLWD4",
        proxy_url="http://127.0.0.1:8004",
        proxy_session_cookie_name=os.environ.get(
            "CDS_REPOSITORY_PROXY_SESSION_COOKIE_NAME",
            "cds_repository_proxy_session",
        ),
    ),
    RemoteServerId.CDS_REPOSITORY_SANDBOX: RemoteServer(
        id=RemoteServerId.CDS_REPOSITORY_SANDBOX,
        label="CDS Sandbox",
        base_url="https://sandbox-cds-rdm.web.cern.ch",
        oauth_client_id="J5nzeas8LpcGllJysNJzj52YT0qpvJbVA0AN0F5y",
        proxy_url="http://127.0.0.1:8005",
        proxy_session_cookie_name=os.environ.get(
            "CDS_REPOSITORY_SANDBOX_PROXY_SESSION_COOKIE_NAME",
            "cds_repository_sandbox_proxy_session",
        ),
    ),
    RemoteServerId.INVENIORDM_LOCAL: RemoteServer(
        id=RemoteServerId.INVENIORDM_LOCAL,
        label="InvenioRDM Local",
        base_url="http://127.0.0.1:80",
        oauth_client_id="jupyterlab-extension",
        proxy_url="http://127.0.0.1:8006",
        proxy_session_cookie_name=os.environ.get(
            "INVENIORDM_LOCAL_PROXY_SESSION_COOKIE_NAME",
            "invenioRDM_local_proxy_session",
        ),
    ),
}


def get_remote_server(server_id: RemoteServerId) -> RemoteServer:
    return _REMOTE_SERVERS[server_id]


def get_remote_servers() -> tuple[RemoteServer, ...]:
    return tuple(_REMOTE_SERVERS.values())


def get_remote_server_by_url(url: str) -> RemoteServer:
    normalized_url = url.rstrip("/")
    for server in _REMOTE_SERVERS.values():
        if normalized_url in {server.base_url, server.proxy_url}:
            return server
    raise ValueError(f"Unknown remote server URL: {url}")
