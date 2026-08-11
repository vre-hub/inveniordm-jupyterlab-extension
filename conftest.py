from pathlib import Path

import pytest
from traitlets.config.loader import PyFileConfigLoader

pytest_plugins = ("pytest_jupyter.jupyter_server",)


@pytest.fixture
def jp_server_config(jp_server_config):
    config = PyFileConfigLoader(
        "jupyter_server_config.py",
        path=str(Path(__file__).parent / "lab_cwd"),
    ).load_config()
    return {
        **jp_server_config,
        "ServerApp": {"jpserver_extensions": {"inveniordm_jupyterlab": True}},
        "InvenioRDMJupyterLab": config["InvenioRDMJupyterLab"],
    }
