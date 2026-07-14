from pathlib import Path
from typing import Any, Protocol

from .zenodo_requests.zenodo import ZenodoFileResponse


class ZenodoFileSource(Protocol):
    """
    Implemented by ZenodoRequests.
    Contains functionality for downloading files and reading file metadata from Zenodo.
    """
    def open_zenodo_file(self, *, file_url: str) -> ZenodoFileResponse:
        ...

    def get_zenodo_record_file(
        self,
        *,
        record_id: int | str,
        file_key: str,
    ) -> dict[str, Any]:
        ...


class ZenodoDownloadLocationManager:
    """
    Resolves Zenodo file download locations on disk.
    """
    def __init__(self, downloads_dir: Path):
        self.downloads_dir = downloads_dir

    def get_download_location(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        record_id: int | str,
        file_key: str,
    ) -> Path:
        file_metadata = zenodo_requests.get_zenodo_record_file(
            record_id=record_id,
            file_key=file_key,
        )
        return self.download_location_from_metadata(
            file_metadata,
            record_id=record_id,
        )

    def find_downloaded_file(
        self,
        *,
        record_id: int | str,
        file_key: str,
    ) -> Path | None:
        """
        Find a downloaded zenodo file on disk, based on the record_id and file_key.
        Returns the path to the file if found, or None if not found.
        """
        safe_record_id = Path(str(record_id)).name
        if not safe_record_id:
            raise ValueError("Missing record_id")
        filestem = self._download_filestem(file_key)

        record_dir = self.downloads_dir / safe_record_id
        if not record_dir.is_dir():
            return None

        for candidate in record_dir.iterdir():
            if not candidate.is_file() or candidate.suffix == ".part":
                continue
            if candidate.name == filestem or candidate.name.startswith(
                f"{filestem}."
            ):
                return candidate

        return None

    def find_downloaded_file_from_metadata(
        self,
        file_metadata: dict[str, Any],
        *,
        record_id: int | str,
    ) -> Path | None:
        """
        Find a downloaded zenodo file on disk, based on the record_id and
        metadata filename.
        """
        safe_record_id = Path(str(record_id)).name
        if not safe_record_id:
            raise ValueError("Missing record_id")
        safe_filename = self._download_filename_from_metadata(file_metadata)

        candidate = self.downloads_dir / safe_record_id / safe_filename
        if candidate.is_file():
            return candidate

        return None

    def remove_empty_parent(self, path: Path) -> None:
        parent = path.parent
        try:
            parent.rmdir()
        except OSError:
            pass

    def download_location_from_metadata(
        self,
        file_metadata: dict[str, Any],
        *,
        record_id: int | str,
    ) -> Path:
        safe_filename = self._download_filename_from_metadata(file_metadata)
        safe_record_id = Path(str(record_id)).name
        if not safe_record_id:
            raise ValueError("Missing record_id")

        return self.downloads_dir / safe_record_id / safe_filename

    def _download_filename_from_metadata(self, file_metadata: dict[str, Any]) -> str:
        filename = (
            file_metadata.get("filename")
            or file_metadata.get("key")
            or file_metadata.get("name")
        )
        if not filename:
            raise ValueError("Missing filename")

        safe_filename = Path(str(filename)).name
        if not safe_filename:
            raise ValueError("Missing filename")

        return safe_filename

    def _download_filestem(self, file_key: str) -> str:
        """
        Get the file stem for a Zenodo file download, based on the file_key.
        The InvenioRDM file key is also the filename.
        """
        safe_file_key = Path(str(file_key)).name
        if not safe_file_key:
            raise ValueError("Missing file_key")

        return safe_file_key
