from pathlib import Path

from .util.job_manager import JobContext, JobManager, ProgressListener
from .util.job_types import JobProgress
from .zenodo_downloads import ZenodoDownloads, ZenodoFileSource


class ZenodoDownloadManager:
    """
    Manages Zenodo file downloads:
    Allows starting and managing downloads for record files.
    """

    def __init__(
        self,
        downloads_dir: Path,
        job_manager: JobManager | None = None,
    ):
        self.zenodo_downloads = ZenodoDownloads(downloads_dir)
        self.job_manager = job_manager or JobManager()

    def start_download(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        record_id: int | str,
        file_key: str,
        on_progress_changed: ProgressListener | None = None,
    ) -> str:
        def download(context: JobContext) -> dict[str, object]:
            destination = self.zenodo_downloads.download_file(
                zenodo_requests,
                record_id=record_id,
                file_key=file_key,
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
                    "record_id": str(record_id),
                    "file_key": file_key,
                },
            ),
            on_progress_changed=on_progress_changed,
            cancel_message="Download canceled",
        )

    def get_progress(self, download_id: str) -> dict[str, object] | None:
        return self.job_manager.get_progress(download_id)

    def cancel(self, download_id: str) -> dict[str, object] | None:
        return self.job_manager.cancel(download_id)

    def get_download_status(
        self,
        *,
        record_id: int | str,
        file_key: str,
    ) -> dict[str, object]:
        return self.zenodo_downloads.get_download_status(
            record_id=record_id,
            file_key=file_key,
        )

    def delete_download(
        self,
        *,
        record_id: int | str,
        file_key: str,
    ) -> dict[str, object]:
        return self.zenodo_downloads.delete_download(
            record_id=record_id,
            file_key=file_key,
        )

    def get_download_location(
        self,
        *,
        record_id: int | str,
        file_key: str,
    ) -> Path:
        return self.zenodo_downloads.get_download_location(
            record_id=record_id,
            file_key=file_key,
        )
