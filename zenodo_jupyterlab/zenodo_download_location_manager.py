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

    def get_zenodo_deposition_file(
        self,
        *,
        deposition_id: int | str,
        file_id: str,
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
        deposition_id: int | str,
        file_id: str,
    ) -> Path:
        file_metadata = zenodo_requests.get_zenodo_deposition_file(
            deposition_id=deposition_id,
            file_id=file_id,
        )
        return self.download_location_from_metadata(
            file_metadata,
            deposition_id=deposition_id,
        )

    def find_downloaded_file(
        self,
        *,
        deposition_id: int | str,
        file_id: str,
    ) -> Path | None:
        """
        Find a downloaded zenodo file on disk, based on the deposition_id and file_id.
        Returns the path to the file if found, or None if not found.
        """
        safe_deposition_id = Path(str(deposition_id)).name
        if not safe_deposition_id:
            raise ValueError("Missing deposition_id")
        filestem = self._download_filestem(file_id)

        deposition_dir = self.downloads_dir / safe_deposition_id
        if not deposition_dir.is_dir():
            return None

        for candidate in deposition_dir.iterdir():
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
        deposition_id: int | str,
    ) -> Path | None:
        """
        Find a downloaded zenodo file on disk, based on the deposition_id and
        metadata filename.
        """
        safe_deposition_id = Path(str(deposition_id)).name
        if not safe_deposition_id:
            raise ValueError("Missing deposition_id")
        safe_filename = self._download_filename_from_metadata(file_metadata)

        candidate = self.downloads_dir / safe_deposition_id / safe_filename
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
        deposition_id: int | str,
    ) -> Path:
        safe_filename = self._download_filename_from_metadata(file_metadata)
        safe_deposition_id = Path(str(deposition_id)).name
        if not safe_deposition_id:
            raise ValueError("Missing deposition_id")

        return self.downloads_dir / safe_deposition_id / safe_filename

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

    def _download_filestem(self, file_id: str) -> str:
        """
        Get the file stem for a Zenodo file download, based on the file_id.
        Currently, this is just the file id.
        """
        safe_file_id = Path(str(file_id)).name
        if not safe_file_id:
            raise ValueError("Missing file_id")

        return safe_file_id
