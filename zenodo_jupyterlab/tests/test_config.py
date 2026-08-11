import pytest
from traitlets.config import Config

from zenodo_auth.remote_servers import RemoteServerRegistry, UnknownRemoteServerError
from zenodo_jupyterlab.config import ZenodoJupyterLab

REMOTE_SERVERS = {
    "zenodo_sandbox": {
        "label": "Sandbox",
        "base_url": "https://sandbox.example/",
        "oauth_client_id": "client-id",
        "proxy_url": "http://proxy.example/",
        "proxy_session_cookie_name": "sandbox_session",
    }
}


def test_reads_remote_servers_from_jupyter_config():
    config = Config(
        {
            "ZenodoJupyterLab": {
                "remote_servers_mode": "extend",
                "remote_servers": {
                    "inveniordm_local": {
                        "label": "InvenioRDM Local",
                        "base_url": "http://127.0.0.1:80",
                        "oauth_client_id": "jupyterlab-extension",
                        "proxy_url": "http://127.0.0.1:8006",
                        "proxy_session_cookie_name": "invenioRDM_local_proxy_session",
                    }
                },
            }
        }
    )

    registry = ZenodoJupyterLab(config=config).remote_server_registry()

    assert {server.id for server in registry.all()} == {
        "zenodo_production",
        "cds_repository",
        "inveniordm_local",
    }
    assert registry.get("zenodo_production").label == "Production"
    assert registry.get("inveniordm_local").proxy_url == "http://127.0.0.1:8006"
    assert registry.default.id == "zenodo_production"


def test_replaces_remote_servers_from_jupyter_config():
    config = Config(
        {
            "ZenodoJupyterLab": {
                "remote_servers_mode": "replace",
                "remote_servers": {
                    "inveniordm_local": {
                        "label": "InvenioRDM Local",
                        "base_url": "http://127.0.0.1:80",
                        "oauth_client_id": "jupyterlab-extension",
                        "proxy_url": "http://127.0.0.1:8006",
                        "proxy_session_cookie_name": "invenioRDM_local_proxy_session",
                    }
                },
            }
        }
    )

    registry = ZenodoJupyterLab(config=config).remote_server_registry()

    assert [server.id for server in registry.all()] == ["inveniordm_local"]
    assert registry.default.id == "inveniordm_local"


def test_uses_configured_default_remote_server_when_present():
    config = Config(
        {
            "ZenodoJupyterLab": {
                "default_remote_server": "zenodo_sandbox",
                "remote_servers": {
                    "zenodo_production": {
                        "label": "Production",
                        "base_url": "https://zenodo.org",
                        "oauth_client_id": "client-id",
                        "proxy_url": "http://proxy.example/",
                        "proxy_session_cookie_name": "production_session",
                    },
                    "zenodo_sandbox": {
                        "label": "Sandbox",
                        "base_url": "https://sandbox.example/",
                        "oauth_client_id": "sandbox-client-id",
                        "proxy_url": "http://sandbox-proxy.example/",
                        "proxy_session_cookie_name": "sandbox_session",
                    },
                },
            }
        }
    )

    registry = ZenodoJupyterLab(config=config).remote_server_registry()

    assert registry.default.id == "zenodo_sandbox"


def test_remote_server_registry_rejects_empty_config():
    with pytest.raises(ValueError, match="must not be empty"):
        RemoteServerRegistry({})


def test_remote_server_registry_rejects_incomplete_server():
    with pytest.raises(ValueError, match="oauth_client_id"):
        RemoteServerRegistry(
            {
                "zenodo_sandbox": {
                    "label": "Sandbox",
                    "base_url": "https://sandbox.example",
                }
            }
        )


def test_remote_server_registry_accepts_config_only_id():
    registry = RemoteServerRegistry(
        {"custom_repository": REMOTE_SERVERS["zenodo_sandbox"]}
    )

    assert registry.default.id == "custom_repository"


def test_remote_server_registry_rejects_unknown_id():
    registry = RemoteServerRegistry(REMOTE_SERVERS)

    with pytest.raises(UnknownRemoteServerError, match="removed-server"):
        registry.get("removed-server")
