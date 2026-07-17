from typing import Any, BinaryIO, Callable

from .job_types import CancelCheck, JobCancelled


class ProgressReportingReader:
    """
    A wrapper around a file-like object that reports progress on reads and checks for cancellation.
    Used for uploading files to Zenodo via JobManager.
    """

    def __init__(
        self,
        file: BinaryIO,
        *,
        on_bytes_read: Callable[[int], None],
        should_cancel: CancelCheck | None = None,
    ):
        self.file = file
        self.on_bytes_read = on_bytes_read
        self.should_cancel = should_cancel

    def read(self, size: int = -1) -> bytes:
        if self.should_cancel is not None and self.should_cancel():
            raise JobCancelled("Upload canceled")
        chunk = self.file.read(size)
        if chunk:
            self.on_bytes_read(len(chunk))
        return chunk

    def tell(self) -> int:
        return self.file.tell()

    def seek(self, offset: int, whence: int = 0) -> int:
        return self.file.seek(offset, whence)

    def fileno(self) -> int:
        return self.file.fileno()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.file, name)
