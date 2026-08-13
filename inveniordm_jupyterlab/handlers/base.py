import json
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from jupyter_core.paths import jupyter_data_dir
from jupyter_server.base.handlers import APIHandler as JupyterAPIHandler

from inveniordm_auth.remote_servers import UnknownRemoteServerError
from inveniordm_jupyterlab.user_settings import InvenioRDMUserSettings
from inveniordm_jupyterlab.util.job_manager import JobManager

from ..inveniordm_download_manager import InvenioRDMDownloadManager
from ..inveniordm_file_identifier import InvenioRDMFileIdentifier
from ..inveniordm_requests.inveniordm_requests import InvenioRDMRequests


class APIHandler(JupyterAPIHandler):
    def write_error(self, status_code: int, **kwargs) -> None:
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


def _contents_root(handler: APIHandler) -> Path:
    contents_manager = handler.settings["contents_manager"]
    return Path(contents_manager.root_dir).resolve()


def _resolve_contents_file_paths(
    handler: APIHandler,
    file_paths: list[str],
) -> list[Path]:
    """
    Convert a list of file paths that are relative to the Jupyter root into absolute paths on the filesystem.
    """
    root_dir = _contents_root(handler)
    resolved_paths = []

    for file_path in file_paths:
        path = (root_dir / file_path).resolve()
        if not path.is_relative_to(root_dir):
            raise ValueError(f"File is outside the Jupyter root: {file_path}")
        if not path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        resolved_paths.append(path)

    return resolved_paths


def get_user_id(handler: APIHandler) -> str:
    """
    Get a unique ID for the current user.
    """
    return handler.current_user.username


def _default_downloads_dir() -> Path:
    return Path(jupyter_data_dir()) / "inveniordm_jupyterlab" / "downloads"


def _download_status_changed_topic(file_id: InvenioRDMFileIdentifier) -> str:
    return (
        "file.download-status.changed."
        f"{quote(str(file_id.record_id), safe='')}."
        f"{quote(file_id.record_status, safe='')}."
        f"{quote(file_id.file_key, safe='')}"
    )


def _record_changed_topic(record_id: int | str) -> str:
    return f"record.changed.{quote(str(record_id), safe='')}"
