import pytest

from inveniordm_auth.remote_servers import RemoteServerRegistry


@pytest.fixture
def remote_servers() -> RemoteServerRegistry:
    return RemoteServerRegistry(
        {
            "zenodo": {
                "label": "Zenodo",
                "base_url": "https://zenodo.org",
                "oauth_client_id": "zenodo-client",
            },
            "cds": {
                "label": "CDS",
                "base_url": "https://repository.cern",
                "oauth_client_id": "cds-client",
            },
        },
        default_server_id="zenodo",
    )
