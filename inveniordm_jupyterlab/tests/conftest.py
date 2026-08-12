from pathlib import Path

import pytest
from traitlets.config.loader import PyFileConfigLoader

from inveniordm_auth.remote_servers import RemoteServerRegistry
from inveniordm_jupyterlab.config import InvenioRDMJupyterLab


@pytest.fixture
def remote_servers() -> RemoteServerRegistry:
    repository_root = Path(__file__).parents[2]
    config = PyFileConfigLoader(
        "jupyter_server_config.py",
        path=str(repository_root / "lab_cwd"),
    ).load_config()
    return InvenioRDMJupyterLab(config=config).remote_server_registry()
