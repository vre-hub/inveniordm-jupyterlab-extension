from pathlib import Path

from inveniordm_auth.remote_servers import RemoteServerId

from .util.job_manager import JobContext, JobManager, ProgressListener
from .util.job_types import JobProgress
from .inveniordm_downloads import InvenioRDMDownloads, InvenioRDMFileSource
from .inveniordm_file_identifier import InvenioRDMFileIdentifier


class InvenioRDMDownloadManager:
    """
    Manages InvenioRDM file downloads:
    Allows starting and managing downloads for record files.
    """

    def __init__(
        self,
        downloads_dir: Path,
        remote_server_id: RemoteServerId,
        job_manager: JobManager | None = None,
    ):
        """Initialize download storage and background-job tracking."""
        self.inveniordm_downloads = InvenioRDMDownloads(downloads_dir, remote_server_id)
        self.job_manager = job_manager or JobManager()

    def start_download(
        self,
        inveniordm_requests: InvenioRDMFileSource,
        *,
        file_id: InvenioRDMFileIdentifier,
        on_progress_changed: ProgressListener | None = None,
    ) -> str:
        """Start a cancellable download job and return its job identifier.

        Progress callbacks receive snapshots updated as response bytes are written.
        The final job result contains the downloaded file's local path.
        """
        def download(context: JobContext) -> dict[str, object]:
            destination = self.inveniordm_downloads.download_file(
                inveniordm_requests,
                file_id=file_id,
                on_progress=lambda bytes_downloaded, total_bytes: context.update(
                    completed_bytes=bytes_downloaded,
                    total_bytes=total_bytes,
                ),
                should_cancel=context.should_cancel,
            )
            return {"path": str(destination)}

        return self.job_manager.start(
            download,
            progress=JobProgress(
                job_type="download",
                metadata={
                    "record_id": str(file_id.record_id),
                    "record_status": file_id.record_status,
                    "file_key": file_id.file_key,
                },
            ),
            on_progress_changed=on_progress_changed,
            cancel_message="Download canceled",
        )

    def get_progress(self, download_id: str) -> dict[str, object] | None:
        """Return the latest progress snapshot for a download."""
        return self.job_manager.get_progress(download_id)

    def cancel(self, download_id: str) -> dict[str, object] | None:
        """Request cancellation of an active download."""
        return self.job_manager.cancel(download_id)

    def get_download_status(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> dict[str, object]:
        """Return whether a remote file has already been downloaded."""
        return self.inveniordm_downloads.get_download_status(
            file_id=file_id,
        )

    def delete_download(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> dict[str, object]:
        """Delete a downloaded file and report the outcome."""
        return self.inveniordm_downloads.delete_download(
            file_id=file_id,
        )

    def get_download_location(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> Path:
        """Return the expected local path for a remote file."""
        return self.inveniordm_downloads.get_download_location(
            file_id=file_id,
        )
