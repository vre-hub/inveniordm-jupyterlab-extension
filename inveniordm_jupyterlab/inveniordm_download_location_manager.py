from pathlib import Path
from typing import Protocol

from inveniordm_auth.remote_servers import RemoteServerId

from .inveniordm_file_identifier import InvenioRDMFileIdentifier
from .inveniordm_requests.inveniordm import InvenioRDMFileResponse


class InvenioRDMFileSource(Protocol):
    """
    Implemented by InvenioRDMRequests.
    Contains functionality for downloading files from InvenioRDM.
    """

    def open_inveniordm_file(
        self, *, file_id: InvenioRDMFileIdentifier
    ) -> InvenioRDMFileResponse: ...


class InvenioRDMDownloadLocationManager:
    """
    Resolves InvenioRDM file download locations on disk.
    """

    def __init__(self, downloads_dir: Path, remote_server_id: RemoteServerId):
        """Initialize paths for one remote server's downloads."""
        self.downloads_dir = downloads_dir
        self.remote_server_id = remote_server_id

    def find_downloaded_file(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> Path | None:
        """
        Find a downloaded InvenioRDM file on disk, based on its full file identifier.
        Returns the path to the file if found, or None if not found.
        """
        candidate = self.download_location(file_id=file_id)
        return candidate if candidate.is_file() else None

    def remove_empty_parent(self, path: Path) -> None:
        """Remove empty record and status directories above a file."""
        for parent in (path.parent, path.parent.parent):
            try:
                parent.rmdir()
            except OSError:
                break

    def download_location(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> Path:
        """Return the safe, server-scoped destination for a remote file."""
        safe_record_id = Path(str(file_id.record_id)).name
        if not safe_record_id:
            raise ValueError("Missing record_id")
        safe_file_key = Path(file_id.file_key).name
        if not safe_file_key:
            raise ValueError("Missing file_key")

        return (
            self.downloads_dir
            / self.remote_server_id
            / safe_record_id
            / file_id.record_status
            / safe_file_key
        )
