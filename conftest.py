import pytest

pytest_plugins = ("pytest_jupyter.jupyter_server",)


@pytest.fixture
def jp_server_config(jp_server_config):
    return {
        **jp_server_config,
        "ServerApp": {"jpserver_extensions": {"inveniordm_jupyterlab": True}},
        "InvenioRDMJupyterLab": {
            "request_mode": "local",
            "remote_servers": {
                "test_repository": {
                    "label": "Test repository",
                    "base_url": "https://repository.example",
                    "oauth_client_id": "test-client",
                }
            },
        },
    }
