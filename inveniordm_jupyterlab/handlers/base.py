import json
from pathlib import Path
from typing import Callable

from jupyter_server.base.handlers import APIHandler as JupyterAPIHandler

from inveniordm_auth.remote_servers import UnknownRemoteServerError
from inveniordm_jupyterlab.user_settings import InvenioRDMUserSettings
from inveniordm_jupyterlab.util.job_manager import JobManager

from ..inveniordm_download_manager import InvenioRDMDownloadManager
from ..inveniordm_requests.inveniordm_requests import InvenioRDMRequests


class APIHandler(JupyterAPIHandler):
    """
    Base APIHandler class for InvenioRDM JupyterLab extension.
    """

    def write_error(self, status_code: int, **kwargs) -> None:
        """
        Override the default write_error method to handle UnknownRemoteServerError exceptions.
        """
        exc_info = kwargs.get("exc_info")
        if exc_info and isinstance(exc_info[1], UnknownRemoteServerError):
            self.set_status(400)
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps({"message": str(exc_info[1])}))
            return
        super().write_error(status_code, **kwargs)


GetInvenioRDMRequests = Callable[[APIHandler], InvenioRDMRequests]
GetInvenioRDMDownloadManager = Callable[[APIHandler], InvenioRDMDownloadManager]
GetJobManager = Callable[[APIHandler], JobManager]
CreateJobMetadata = Callable[[InvenioRDMRequests], dict[str, object]]
GetUserSettings = Callable[[APIHandler], InvenioRDMUserSettings]


def contents_root(handler: APIHandler) -> Path:
    """Return the resolved root managed by Jupyter's contents service."""
    contents_manager = handler.settings["contents_manager"]
    return Path(contents_manager.root_dir).resolve()


def get_user_id(handler: APIHandler) -> str:
    """
    Get a unique ID for the current user.
    """
    return handler.current_user.username
