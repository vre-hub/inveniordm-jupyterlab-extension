from typing import Callable


ProgressCallback = Callable[[int, int | None], None]
CancelCheck = Callable[[], bool]


class DownloadCancelled(Exception):
    pass
