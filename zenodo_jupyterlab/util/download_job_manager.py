from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Callable
from uuid import uuid4

import tornado.ioloop

from .download_types import CancelCheck, DownloadCancelled, ProgressCallback


DownloadCallable = Callable[[ProgressCallback, CancelCheck], Path]
ProgressListener = Callable[[str, dict[str, object]], None]


class DownloadJobManager:
    """
    Manages general download jobs: Allows running downloads in the background,
    tracking their progress and allowing cancellation.
    """
    def __init__(self):
        self.progress_store = DownloadProgressStore()
        self._progress_listeners: dict[str, ProgressListener] = {}

    def start_download(
        self,
        download: DownloadCallable,
        *,
        on_progress_changed: ProgressListener | None = None,
    ) -> str:
        download_id = self.progress_store.create()
        io_loop = tornado.ioloop.IOLoop.current()
        if on_progress_changed is not None:
            self._progress_listeners[download_id] = on_progress_changed

        async def run_download():
            self.progress_store.update(download_id, status="running")
            self._notify_progress_changed(
                download_id,
                io_loop,
                on_progress_changed,
            )

            def on_progress(bytes_downloaded: int, total_bytes: int | None) -> None:
                self.progress_store.update(
                    download_id,
                    bytes_downloaded=bytes_downloaded,
                    total_bytes=total_bytes,
                )
                self._notify_progress_changed(
                    download_id,
                    io_loop,
                    on_progress_changed,
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
                self._notify_progress_changed(
                    download_id,
                    io_loop,
                    on_progress_changed,
                )
                self._progress_listeners.pop(download_id, None)
                return
            except Exception as error:
                self.progress_store.update(
                    download_id,
                    status="error",
                    message=str(error),
                )
                self._notify_progress_changed(
                    download_id,
                    io_loop,
                    on_progress_changed,
                )
                self._progress_listeners.pop(download_id, None)
                return

            self.progress_store.update(
                download_id,
                status="done",
                path=str(destination),
            )
            self._notify_progress_changed(
                download_id,
                io_loop,
                on_progress_changed,
            )
            self._progress_listeners.pop(download_id, None)

        tornado.ioloop.IOLoop.current().spawn_callback(run_download)
        return download_id

    def get_progress(self, download_id: str) -> dict[str, object] | None:
        return self.progress_store.get(download_id)

    def cancel(self, download_id: str) -> dict[str, object] | None:
        progress = self.progress_store.request_cancel(download_id)
        if progress is not None:
            self._notify_progress_changed(
                download_id,
                tornado.ioloop.IOLoop.current(),
                self._progress_listeners.get(download_id),
                progress=progress,
            )
        return progress

    def _notify_progress_changed(
        self,
        download_id: str,
        io_loop: tornado.ioloop.IOLoop,
        on_progress_changed: ProgressListener | None,
        *,
        progress: dict[str, object] | None = None,
    ) -> None:
        if on_progress_changed is None:
            return

        progress = progress or self.progress_store.get(download_id)
        if progress is None:
            return

        io_loop.add_callback(on_progress_changed, download_id, progress)



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
