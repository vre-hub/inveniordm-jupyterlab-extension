from pathlib import Path
from typing import Any, Protocol

from .zenodo import ZenodoFileResponse


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


class DownloadManager:
    def __init__(self, downloads_dir: Path):
        self.downloads_dir = downloads_dir

    def download_zenodo_file(
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
        file_url = (
            file_metadata.get("links", {}).get("download")
            or file_metadata.get("links", {}).get("content")
        )
        filename = (
            file_metadata.get("filename")
            or file_metadata.get("key")
            or file_metadata.get("name")
        )
        if not file_url or not filename:
            raise ValueError("Missing file download metadata")

        response = zenodo_requests.open_zenodo_file(file_url=file_url)
        try:
            return self._save_response(response, filename, deposition_id)
        finally:
            response.close()

    def _save_response(
        self,
        response: ZenodoFileResponse,
        filename: str,
        deposition_id: int | str,
    ) -> Path:
        safe_filename = Path(filename).name
        if not safe_filename:
            raise ValueError("Missing filename")
        safe_deposition_id = Path(str(deposition_id)).name
        if not safe_deposition_id:
            raise ValueError("Missing deposition_id")

        deposition_downloads_dir = self.downloads_dir / safe_deposition_id
        deposition_downloads_dir.mkdir(parents=True, exist_ok=True)
        destination = deposition_downloads_dir / safe_filename
        with destination.open("wb") as file:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

        return destination
