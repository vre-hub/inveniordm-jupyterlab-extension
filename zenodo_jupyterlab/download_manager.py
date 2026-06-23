from pathlib import Path
from typing import Protocol

from .zenodo import ZenodoFileResponse


class ZenodoFileSource(Protocol):
    def open_zenodo_file(self, *, file_url: str) -> ZenodoFileResponse:
        ...


class DownloadManager:
    def __init__(self, downloads_dir: Path):
        self.downloads_dir = downloads_dir

    def download_zenodo_file(
        self,
        zenodo_requests: ZenodoFileSource,
        *,
        file_url: str,
        filename: str,
    ) -> Path:
        response = zenodo_requests.open_zenodo_file(file_url=file_url)
        try:
            return self._save_response(response, filename)
        finally:
            response.close()

    def _save_response(self, response: ZenodoFileResponse, filename: str) -> Path:
        safe_filename = Path(filename).name
        if not safe_filename:
            raise ValueError("Missing filename")

        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        destination = self.downloads_dir / safe_filename
        with destination.open("wb") as file:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

        return destination
