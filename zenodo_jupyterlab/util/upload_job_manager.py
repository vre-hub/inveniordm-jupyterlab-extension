from dataclasses import asdict, dataclass
from threading import Lock
from typing import Callable
from uuid import uuid4

import tornado.ioloop


UploadProgressCallback = Callable[[int, int, str | None], None]
UploadCallable = Callable[[UploadProgressCallback], dict[str, object]]
ProgressListener = Callable[[str, dict[str, object]], None]


class UploadJobManager:
    """
    Run Zenodo uploads in the background and track upload progress.
    """
    def __init__(self):
        self.progress_store = UploadProgressStore()

    def start_upload(
        self,
        upload: UploadCallable,
        *,
        on_progress_changed: ProgressListener | None = None,
    ) -> str:
        upload_id = self.progress_store.create()
        io_loop = tornado.ioloop.IOLoop.current()

        async def run_upload():
            self.progress_store.update(upload_id, status="running")
            self._notify_progress_changed(upload_id, io_loop, on_progress_changed)

            def on_progress(
                bytes_uploaded: int,
                total_bytes: int,
                current_file: str | None = None,
            ) -> None:
                self.progress_store.update(
                    upload_id,
                    bytes_uploaded=bytes_uploaded,
                    total_bytes=total_bytes,
                    current_file=current_file,
                )
                self._notify_progress_changed(upload_id, io_loop, on_progress_changed)

            try:
                deposition = await tornado.ioloop.IOLoop.current().run_in_executor(
                    None,
                    lambda: upload(on_progress),
                )
            except Exception as error:
                self.progress_store.update(
                    upload_id,
                    status="error",
                    message=str(error),
                )
                self._notify_progress_changed(upload_id, io_loop, on_progress_changed)
                return

            self.progress_store.update(
                upload_id,
                status="done",
                deposition=deposition,
            )
            self._notify_progress_changed(upload_id, io_loop, on_progress_changed)

        tornado.ioloop.IOLoop.current().spawn_callback(run_upload)
        return upload_id

    def get_progress(self, upload_id: str) -> dict[str, object] | None:
        return self.progress_store.get(upload_id)

    def _notify_progress_changed(
        self,
        upload_id: str,
        io_loop: tornado.ioloop.IOLoop,
        on_progress_changed: ProgressListener | None,
    ) -> None:
        if on_progress_changed is None:
            return

        progress = self.progress_store.get(upload_id)
        if progress is None:
            return

        io_loop.add_callback(on_progress_changed, upload_id, progress)


@dataclass
class UploadProgress:
    status: str
    bytes_uploaded: int = 0
    total_bytes: int = 0
    current_file: str | None = None
    message: str | None = None
    deposition: dict[str, object] | None = None


class UploadProgressStore:
    def __init__(self):
        self._progress: dict[str, UploadProgress] = {}
        self._lock = Lock()

    def create(self) -> str:
        upload_id = uuid4().hex
        with self._lock:
            self._progress[upload_id] = UploadProgress(status="pending")
        return upload_id

    def update(self, upload_id: str, **changes) -> None:
        with self._lock:
            progress = self._progress[upload_id]
            for key, value in changes.items():
                setattr(progress, key, value)

    def get(self, upload_id: str) -> dict[str, object] | None:
        with self._lock:
            progress = self._progress.get(upload_id)
            return asdict(progress) if progress is not None else None
