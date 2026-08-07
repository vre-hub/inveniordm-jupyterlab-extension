from pathlib import Path

import pytest
from traitlets.config.loader import PyFileConfigLoader

from zenodo_auth.remote_servers import RemoteServerRegistry


@pytest.fixture
def remote_servers() -> RemoteServerRegistry:
    repository_root = Path(__file__).parents[2]
    config = PyFileConfigLoader(
        "jupyter_server_config.py",
        path=str(repository_root / "lab_cwd"),
    ).load_config()
    return RemoteServerRegistry(config["ZenodoJupyterLab"]["remote_servers"])
