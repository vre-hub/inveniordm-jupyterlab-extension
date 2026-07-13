from dataclasses import dataclass, field
from typing import Callable


CancelCheck = Callable[[], bool]
UploadProgressCallback = Callable[[int, int, str | None], None]
DownloadProgressCallback = Callable[[int, int | None], None]


class JobCancelled(Exception):
    pass


@dataclass
class JobProgress:
    job_type: str
    metadata: dict[str, object] = field(default_factory=dict)
    job_id: str = ""
    status: str = "pending"
    completed_bytes: int = 0
    total_bytes: int | None = None
    current_item: str | None = None
    message: str | None = None
    result: dict[str, object] | None = None
    cancel_requested: bool = False
