from dataclasses import dataclass
from typing import Callable


CancelCheck = Callable[[], bool]
UploadProgressCallback = Callable[[int, int, str | None], None]
DownloadProgressCallback = Callable[[int, int | None], None]


class JobCancelled(Exception):
    pass


@dataclass
class UploadProgress:
    status: str = "pending"
    bytes_uploaded: int = 0
    total_bytes: int = 0
    current_file: str | None = None
    message: str | None = None
    deposition: dict[str, object] | None = None
    cancel_requested: bool = False


@dataclass
class DownloadProgress:
    status: str = "pending"
    bytes_downloaded: int = 0
    total_bytes: int | None = None
    path: str | None = None
    message: str | None = None
    cancel_requested: bool = False


JobProgress = UploadProgress | DownloadProgress
