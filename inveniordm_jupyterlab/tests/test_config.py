import pytest
from traitlets.config import Config

from inveniordm_auth.remote_servers import (
    RemoteServerRegistry,
    UnknownRemoteServerError,
)
from inveniordm_jupyterlab.config import InvenioRDMJupyterLab

REMOTE_SERVERS = {
    "inveniordm_sandbox": {
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
            "InvenioRDMJupyterLab": {
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

    registry = InvenioRDMJupyterLab(config=config).remote_server_registry()

    assert [server.id for server in registry.all()] == ["inveniordm_local"]
    assert registry.get("inveniordm_local").proxy_url == "http://127.0.0.1:8006"
    assert registry.default.id == "inveniordm_local"


def test_request_mode_defaults_to_local():
    assert InvenioRDMJupyterLab().request_mode == "local"


def test_uses_builtin_public_remote_servers_by_default():
    registry = InvenioRDMJupyterLab().remote_server_registry()

    assert [server.id for server in registry.all()] == [
        "zenodo",
        "cds",
    ]
    assert registry.default.base_url == "https://zenodo.org"
    assert registry.default.oauth_client_id == (
        "5LkeWfl5Yvhiz42JkAYQI64UYAsyxll2opUsNdmN"
    )


def test_reads_request_mode_from_jupyter_config():
    config = Config({"InvenioRDMJupyterLab": {"request_mode": "proxy"}})

    assert InvenioRDMJupyterLab(config=config).request_mode == "proxy"


def test_local_request_mode_does_not_require_proxy_settings():
    config = Config(
        {
            "InvenioRDMJupyterLab": {
                "request_mode": "local",
                "remote_servers": {
                    "inveniordm_local": {
                        "label": "InvenioRDM Local",
                        "base_url": "http://127.0.0.1:80",
                        "oauth_client_id": "jupyterlab-extension",
                    }
                },
            }
        }
    )

    server = InvenioRDMJupyterLab(config=config).remote_server_registry().default

    assert server.proxy_url == ""
    assert server.proxy_session_cookie_name == ""


@pytest.mark.parametrize("missing_field", ["proxy_url", "proxy_session_cookie_name"])
def test_proxy_request_mode_requires_proxy_settings(missing_field):
    remote_server = dict(REMOTE_SERVERS["inveniordm_sandbox"])
    del remote_server[missing_field]
    config = Config(
        {
            "InvenioRDMJupyterLab": {
                "request_mode": "proxy",
                "remote_servers": {"inveniordm_sandbox": remote_server},
            }
        }
    )

    with pytest.raises(ValueError, match=missing_field):
        InvenioRDMJupyterLab(config=config).remote_server_registry()


def test_replaces_builtin_remote_servers_from_jupyter_config():
    config = Config(
        {
            "InvenioRDMJupyterLab": {
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

    registry = InvenioRDMJupyterLab(config=config).remote_server_registry()

    assert [server.id for server in registry.all()] == ["inveniordm_local"]
    assert registry.default.id == "inveniordm_local"


def test_uses_configured_default_remote_server_when_present():
    config = Config(
        {
            "InvenioRDMJupyterLab": {
                "default_remote_server": "inveniordm_sandbox",
                "remote_servers": {
                    "inveniordm_production": {
                        "label": "Production",
                        "base_url": "https://inveniordm.org",
                        "oauth_client_id": "client-id",
                        "proxy_url": "http://proxy.example/",
                        "proxy_session_cookie_name": "production_session",
                    },
                    "inveniordm_sandbox": {
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

    registry = InvenioRDMJupyterLab(config=config).remote_server_registry()

    assert registry.default.id == "inveniordm_sandbox"


def test_remote_server_registry_rejects_empty_config():
    with pytest.raises(ValueError, match="must not be empty"):
        RemoteServerRegistry({})


def test_remote_server_registry_rejects_incomplete_server():
    with pytest.raises(ValueError, match="base_url"):
        RemoteServerRegistry(
            {
                "inveniordm_sandbox": {
                    "label": "Sandbox",
                }
            }
        )


@pytest.mark.parametrize("oauth_client_id", [None, "", "  "])
def test_remote_server_registry_accepts_server_without_oauth(oauth_client_id):
    registry = RemoteServerRegistry(
        {
            "public_repository": {
                "label": "Public repository",
                "base_url": "https://public.example",
                "oauth_client_id": oauth_client_id,
            }
        }
    )

    assert registry.default.oauth_client_id is None


def test_remote_server_registry_accepts_config_only_id():
    registry = RemoteServerRegistry(
        {"custom_repository": REMOTE_SERVERS["inveniordm_sandbox"]}
    )

    assert registry.default.id == "custom_repository"


def test_remote_server_registry_rejects_unknown_id():
    registry = RemoteServerRegistry(REMOTE_SERVERS)

    with pytest.raises(UnknownRemoteServerError, match="removed-server"):
        registry.get("removed-server")
