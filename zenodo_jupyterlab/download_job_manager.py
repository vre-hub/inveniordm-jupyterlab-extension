from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Callable
from uuid import uuid4

import tornado.ioloop

from .download_types import CancelCheck, DownloadCancelled, ProgressCallback


DownloadCallable = Callable[[ProgressCallback, CancelCheck], Path]


class DownloadJobManager:
    """
    Manages general download jobs: Allows running downloads in the background,
    tracking their progress and allowing cancellation.
    """
    def __init__(self):
        self.progress_store = DownloadProgressStore()

    def start_download(self, download: DownloadCallable) -> str:
        download_id = self.progress_store.create()

        async def run_download():
            self.progress_store.update(download_id, status="running")

            def on_progress(bytes_downloaded: int, total_bytes: int | None) -> None:
                self.progress_store.update(
                    download_id,
                    bytes_downloaded=bytes_downloaded,
                    total_bytes=total_bytes,
                )

            def should_cancel() -> bool:
                return self.progress_store.cancel_requested(download_id)

            try:
                destination = await tornado.ioloop.IOLoop.current().run_in_executor(
                    None,
                    lambda: download(on_progress, should_cancel),
                )
            except DownloadCancelled:
                self.progress_store.update(
                    download_id,
                    status="canceled",
                    message="Download canceled",
                )
                return
            except Exception as error:
                self.progress_store.update(
                    download_id,
                    status="error",
                    message=str(error),
                )
                return

            self.progress_store.update(
                download_id,
                status="done",
                path=str(destination),
            )

        tornado.ioloop.IOLoop.current().spawn_callback(run_download)
        return download_id

    def get_progress(self, download_id: str) -> dict[str, object] | None:
        return self.progress_store.get(download_id)

    def cancel(self, download_id: str) -> dict[str, object] | None:
        return self.progress_store.request_cancel(download_id)



@dataclass
class DownloadProgress:
    status: str
    bytes_downloaded: int = 0
    total_bytes: int | None = None
    path: str | None = None
    message: str | None = None
    cancel_requested: bool = False


class DownloadProgressStore:
    def __init__(self):
        self._progress: dict[str, DownloadProgress] = {}
        self._lock = Lock()

    def create(self) -> str:
        download_id = uuid4().hex
        with self._lock:
            self._progress[download_id] = DownloadProgress(status="pending")
        return download_id

    def update(self, download_id: str, **changes) -> None:
        with self._lock:
            progress = self._progress[download_id]
            for key, value in changes.items():
                setattr(progress, key, value)

    def request_cancel(self, download_id: str) -> dict[str, object] | None:
        with self._lock:
            progress = self._progress.get(download_id)
            if progress is None:
                return None
            if progress.status in {"done", "error", "canceled"}:
                return asdict(progress)

            progress.cancel_requested = True
            progress.status = "canceling"
            return asdict(progress)

    def cancel_requested(self, download_id: str) -> bool:
        with self._lock:
            progress = self._progress.get(download_id)
            return bool(progress and progress.cancel_requested)

    def get(self, download_id: str) -> dict[str, object] | None:
        with self._lock:
            progress = self._progress.get(download_id)
            return asdict(progress) if progress is not None else None
