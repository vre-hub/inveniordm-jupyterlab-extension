from pathlib import Path

from .util.job_types import (
    CancelCheck,
    DownloadProgressCallback,
    JobCancelled,
)
from .zenodo_download_location_manager import (
    ZenodoDownloadLocationManager,
    ZenodoFileSource,
)
from .zenodo_requests.zenodo import ZenodoFileResponse


class ZenodoDownloads:
    """
    Resolves Zenodo file download locations and writes downloaded files to disk.
    """
    def __init__(self, downloads_dir: Path):
        self.location_manager = ZenodoDownloadLocationManager(
            downloads_dir
        )

    def get_download_location(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        record_id: int | str,
        file_key: str,
    ) -> Path:
        return self.location_manager.get_download_location(
            zenodo_requests,
            record_id=record_id,
            file_key=file_key,
        )

    def get_download_status(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        record_id: int | str,
        file_key: str,
    ) -> dict[str, object]:
        file_metadata = zenodo_requests.get_zenodo_record_file(
            record_id=record_id,
            file_key=file_key,
        )
        existing_file = self.location_manager.find_downloaded_file_from_metadata(
            file_metadata,
            record_id=record_id,
        )
        return {
            "downloaded": existing_file is not None,
            "path": str(existing_file) if existing_file is not None else None,
        }

    def delete_download(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        record_id: int | str,
        file_key: str,
    ) -> dict[str, object]:
        file_metadata = zenodo_requests.get_zenodo_record_file(
            record_id=record_id,
            file_key=file_key,
        )
        existing_file = self.location_manager.find_downloaded_file_from_metadata(
            file_metadata,
            record_id=record_id,
        )
        if existing_file is None:
            return {"deleted": False, "path": None}

        existing_file.unlink()
        self.location_manager.remove_empty_parent(existing_file)
        return {"deleted": True, "path": str(existing_file)}

    def download_file(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        record_id: int | str,
        file_key: str,
        on_progress: DownloadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> Path:
        file_metadata = zenodo_requests.get_zenodo_record_file(
            record_id=record_id,
            file_key=file_key,
        )
        file_url = (
            file_metadata.get("links", {}).get("download")
            or file_metadata.get("links", {}).get("content")
        )
        if not file_url:
            raise ValueError("Missing file download metadata")
        destination = self.location_manager.download_location_from_metadata(
            file_metadata,
            record_id=record_id,
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

    def _save_response(
        self,
        response: ZenodoFileResponse,
        destination: Path,
        *,
        on_progress: DownloadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> Path:
        bytes_downloaded = 0
        total_bytes = response.content_length
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_destination = destination.with_name(f"{destination.name}.part")

        try:
            with temporary_destination.open("wb") as file:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    if should_cancel is not None and should_cancel():
                        raise JobCancelled("Download canceled")
                    if chunk:
                        file.write(chunk)
                        bytes_downloaded += len(chunk)
                        if on_progress is not None:
                            on_progress(bytes_downloaded, total_bytes)
            temporary_destination.replace(destination)
        except JobCancelled:
            temporary_destination.unlink(missing_ok=True)
            raise

        return destination
