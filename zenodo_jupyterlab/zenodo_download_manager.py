from pathlib import Path

from .util.download_job_manager import DownloadJobManager
from .zenodo_downloads import ZenodoDownloads, ZenodoFileSource


class ZenodoDownloadManager:
    """
    Manages Zenodo file downloads:
    Allows starting and managing downloads for deposition files.
    """
    def __init__(
        self,
        downloads_dir: Path,
        zenodo_downloads: ZenodoDownloads | None = None,
        download_job_manager: DownloadJobManager | None = None,
    ):
        self.zenodo_downloads = zenodo_downloads or ZenodoDownloads(downloads_dir)
        self.download_job_manager = download_job_manager or DownloadJobManager()

    def start_download(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        deposition_id: int | str,
        file_id: str,
    ) -> str:
        return self.download_job_manager.start_download(
            lambda on_progress, should_cancel: self.zenodo_downloads.download_file(
                zenodo_requests,
                deposition_id=deposition_id,
                file_id=file_id,
                on_progress=on_progress,
                should_cancel=should_cancel,
            )
        )

    def get_progress(self, download_id: str) -> dict[str, object] | None:
        return self.download_job_manager.get_progress(download_id)

    def cancel(self, download_id: str) -> dict[str, object] | None:
        return self.download_job_manager.cancel(download_id)

    def get_download_status(
        self,
        *,
        deposition_id: int | str,
        file_id: str,
    ) -> dict[str, object]:
        return self.zenodo_downloads.get_download_status(
            deposition_id=deposition_id,
            file_id=file_id,
        )

    def get_download_location(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        deposition_id: int | str,
        file_id: str,
    ) -> Path:
        return self.zenodo_downloads.get_download_location(
            zenodo_requests,
            deposition_id=deposition_id,
            file_id=file_id,
        )
