from pathlib import Path
from typing import Protocol

from .zenodo_file_identifier import ZenodoFileIdentifier
from .zenodo_requests.zenodo import ZenodoFileResponse


class ZenodoFileSource(Protocol):
    """
    Implemented by ZenodoRequests.
    Contains functionality for downloading files from Zenodo.
    """

    def open_zenodo_file(
        self, *, file_id: ZenodoFileIdentifier
    ) -> ZenodoFileResponse: ...


class ZenodoDownloadLocationManager:
    """
    Resolves Zenodo file download locations on disk.
    """

    def __init__(self, downloads_dir: Path):
        self.downloads_dir = downloads_dir

    def find_downloaded_file(
        self,
        *,
        file_id: ZenodoFileIdentifier,
    ) -> Path | None:
        """
        Find a downloaded Zenodo file on disk, based on its full file identifier.
        Returns the path to the file if found, or None if not found.
        """
        candidate = self.download_location(file_id=file_id)
        return candidate if candidate.is_file() else None

    def remove_empty_parent(self, path: Path) -> None:
        for parent in (path.parent, path.parent.parent):
            try:
                parent.rmdir()
            except OSError:
                break

    def download_location(
        self,
        *,
        file_id: ZenodoFileIdentifier,
    ) -> Path:
        safe_record_id = Path(str(file_id.record_id)).name
        if not safe_record_id:
            raise ValueError("Missing record_id")
        safe_file_key = Path(file_id.file_key).name
        if not safe_file_key:
            raise ValueError("Missing file_key")

        return (
            self.downloads_dir
            / safe_record_id
            / file_id.record_status
            / safe_file_key
        )
