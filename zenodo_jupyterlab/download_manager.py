from pathlib import Path
from typing import Any, Protocol

from .download_types import CancelCheck, DownloadCancelled, ProgressCallback
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
    """
    Manages Zenodo file downloads:
    Provides methods to download files using ZenodoRequests
    and writes them to disk.
    """
    def __init__(self, downloads_dir: Path):
        self.downloads_dir = downloads_dir

    def get_zenodo_download_location(
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
        return self._download_location_from_metadata(file_metadata, deposition_id)

    def download_zenodo_file(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        deposition_id: int | str,
        file_id: str,
        on_progress: ProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> Path:
        file_metadata = zenodo_requests.get_zenodo_deposition_file(
            deposition_id=deposition_id,
            file_id=file_id,
        )
        file_url = (
            file_metadata.get("links", {}).get("download")
            or file_metadata.get("links", {}).get("content")
        )
        if not file_url:
            raise ValueError("Missing file download metadata")
        destination = self._download_location_from_metadata(
            file_metadata,
            deposition_id,
        )

        response = zenodo_requests.open_zenodo_file(file_url=file_url)
        try:
            return self._save_response(
                response,
                destination,
                on_progress=on_progress,
                should_cancel=should_cancel,
            )
        finally:
            response.close()

    def _download_location_from_metadata(
        self,
        file_metadata: dict[str, Any],
        deposition_id: int | str,
    ) -> Path:
        """
        Compute the destination path for a Zenodo file download
        from its metadata.
        """
        filename = (
            file_metadata.get("filename")
            or file_metadata.get("key")
            or file_metadata.get("name")
        )
        if not filename:
            raise ValueError("Missing filename")

        safe_filename = Path(filename).name
        if not safe_filename:
            raise ValueError("Missing filename")
        safe_deposition_id = Path(str(deposition_id)).name
        if not safe_deposition_id:
            raise ValueError("Missing deposition_id")

        return self.downloads_dir / safe_deposition_id / safe_filename

    def _save_response(
        self,
        response: ZenodoFileResponse,
        destination: Path,
        *,
        on_progress: ProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> Path:
        """
        Save a streaming response to a file,
        with optional progress reporting and cancellation.
        Writes to a temporary file first so that incomplete downloads do not overwrite existing files.
        """
        bytes_downloaded = 0
        total_bytes = response.content_length
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_destination = destination.with_name(f"{destination.name}.part")

        try:
            with temporary_destination.open("wb") as file:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    if should_cancel is not None and should_cancel():
                        raise DownloadCancelled("Download canceled")
                    if chunk:
                        file.write(chunk)
                        bytes_downloaded += len(chunk)
                        if on_progress is not None:
                            on_progress(bytes_downloaded, total_bytes)
            temporary_destination.replace(destination)
        except DownloadCancelled:
            temporary_destination.unlink(missing_ok=True)
            raise

        return destination
