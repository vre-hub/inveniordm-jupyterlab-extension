from pathlib import Path

from inveniordm_auth.remote_servers import RemoteServerId

from .util.job_types import (
    CancelCheck,
    DownloadProgressCallback,
    JobCancelled,
)
from .inveniordm_download_location_manager import (
    InvenioRDMDownloadLocationManager,
    InvenioRDMFileSource,
)
from .inveniordm_file_identifier import InvenioRDMFileIdentifier
from .inveniordm_requests.inveniordm import InvenioRDMFileResponse


class InvenioRDMDownloads:
    """
    Resolves InvenioRDM file download locations and writes downloaded files to disk.
    """

    def __init__(self, downloads_dir: Path, remote_server_id: RemoteServerId):
        """Initialize download storage for a remote server."""
        self.location_manager = InvenioRDMDownloadLocationManager(
            downloads_dir, remote_server_id
        )

    def get_download_location(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> Path:
        """Return the expected local path for a remote file."""
        return self.location_manager.download_location(
            file_id=file_id,
        )

    def get_download_status(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> dict[str, object]:
        """Return the local download status for a remote file."""
        existing_file = self.location_manager.find_downloaded_file(
            file_id=file_id,
        )
        return {
            "downloaded": existing_file is not None,
            "path": str(existing_file) if existing_file is not None else None,
        }

    def delete_download(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> dict[str, object]:
        """Delete a local download and prune its empty directories."""
        existing_file = self.location_manager.find_downloaded_file(
            file_id=file_id,
        )
        if existing_file is None:
            return {"deleted": False, "path": None}

        existing_file.unlink()
        self.location_manager.remove_empty_parent(existing_file)
        return {"deleted": True, "path": str(existing_file)}

    def download_file(
        self,
        inveniordm_requests: InvenioRDMFileSource,
        *,
        file_id: InvenioRDMFileIdentifier,
        on_progress: DownloadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> Path:
        """Download a file, report progress, and close the remote response."""
        destination = self.location_manager.download_location(
            file_id=file_id,
        )

        response = inveniordm_requests.open_inveniordm_file(file_id=file_id)
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
        response: InvenioRDMFileResponse,
        destination: Path,
        *,
        on_progress: DownloadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> Path:
        """Atomically persist a streamed response to its final destination.

        Bytes are first written to a ``.part`` file so incomplete downloads never
        appear as finished files. Cancellation removes that temporary file before
        propagating the cancellation signal.
        """
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
