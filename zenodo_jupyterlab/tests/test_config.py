import pytest
from traitlets.config import Config

from zenodo_auth.remote_servers import RemoteServerRegistry
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
    config = Config({"ZenodoJupyterLab": {"remote_servers": REMOTE_SERVERS}})

    registry = ZenodoJupyterLab(config=config).remote_server_registry()

    server = registry.get("zenodo_sandbox")
    assert server.label == "Sandbox"
    assert server.base_url == "https://sandbox.example"
    assert server.proxy_url == "http://proxy.example"
    assert registry.default == server


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
