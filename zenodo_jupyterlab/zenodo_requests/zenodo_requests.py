from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Callable

from ..util.job_types import CancelCheck, JobCancelled, UploadProgressCallback
from .zenodo_helpers import include_zenodo_files
from .zenodo import (
    ZenodoFileResponse,
    create_zenodo_deposition,
    get_zenodo_deposition_file,
    get_zenodo_me,
    list_zenodo_depositions,
    open_zenodo_file,
    search_zenodo_records,
    upload_zenodo_deposition_file,
)


@dataclass
class AccessTokenStatus:
    access_token_present: bool
    access_token_valid: bool
    sandbox: bool


class ProgressReportingReader:
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


class ZenodoRequests:
    """
    Wrapper around Zenodo API requests for a specific user/token,
    using caller-provided headers for authentication.
    """
    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ):
        self.url = url.rstrip("/")
        self.headers = headers or {}

    def get_zenodo_me(self) -> dict[str, Any]:
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        return get_zenodo_me(
            base_url=self.url,
            headers=self.headers,
        )

    def search_zenodo_records(
        self,
        *,
        query: str,
        page: int = 1,
        size: int = 10,
        sort: str = "bestmatch",
        all_versions: bool = False,
        filters: dict[str, str] | None = None,
        include_files: bool = False,
    ) -> dict[str, Any]:
        records = search_zenodo_records(
            query,
            base_url=self.url,
            headers=self.headers,
            page=page,
            size=size,
            sort=sort,
            all_versions=all_versions,
            filters=filters,
        )
        if include_files:
            include_zenodo_files(
                records.get("hits", {}).get("hits", []),
                base_url=self.url,
                headers=self.headers,
            )

        return records

    def list_zenodo_depositions(
        self,
        *,
        page: int = 1,
        size: int = 10,
        include_files: bool = False,
    ) -> list[dict[str, Any]]:
        depositions = list_zenodo_depositions(
            base_url=self.url,
            headers=self.headers,
            page=page,
            size=size,
        )
        if include_files:
            include_zenodo_files(
                depositions,
                base_url=self.url,
                headers=self.headers,
            )

        return depositions

    def upload_files_to_bucket(
        self,
        file_paths: list[Path],
        bucket_url: str,
        on_upload_progress: UploadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ):
        """
        Upload files on the local filesystem to a Zenodo deposition bucket.
        """
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        filenames = [path.name for path in file_paths]
        if len(filenames) != len(set(filenames)):
            raise ValueError("Selected files must have unique filenames")

        total_bytes = sum(path.stat().st_size for path in file_paths)
        bytes_uploaded = 0
        if on_upload_progress is not None:
            on_upload_progress(bytes_uploaded, total_bytes, None)

        for path in file_paths:
            if should_cancel is not None and should_cancel():
                raise JobCancelled("Upload canceled")
            with path.open("rb") as file:
                def on_bytes_read(
                    chunk_size: int,
                    *,
                    current_file: str = path.name,
                ) -> None:
                    nonlocal bytes_uploaded
                    bytes_uploaded += chunk_size
                    if on_upload_progress is not None:
                        on_upload_progress(
                            bytes_uploaded,
                            total_bytes,
                            current_file,
                        )

                upload_zenodo_deposition_file(
                    bucket_url,
                    base_url=self.url,
                    headers=self.headers,
                    filename=path.name,
                    content=ProgressReportingReader(
                        file,
                        on_bytes_read=on_bytes_read,
                        should_cancel=should_cancel,
                    ),
                )

    def create_minimal_deposition_draft(
        self,
        *,
        file_paths: list[Path],
        on_upload_progress: UploadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> dict[str, Any]:
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        if should_cancel is not None and should_cancel():
            raise JobCancelled("Upload canceled")

        deposition = create_zenodo_deposition(
            base_url=self.url,
            headers=self.headers,
        )
        if should_cancel is not None and should_cancel():
            raise JobCancelled("Upload canceled")
        bucket_url = deposition["links"]["bucket"]

        self.upload_files_to_bucket(
            file_paths=file_paths,
            bucket_url=bucket_url,
            on_upload_progress=on_upload_progress,
            should_cancel=should_cancel,
        )
        return deposition

    def open_zenodo_file(
        self,
        *,
        file_url: str,
    ) -> ZenodoFileResponse:
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        return open_zenodo_file(
            file_url,
            base_url=self.url,
            headers=self.headers,
        )

    def get_zenodo_deposition_file(
        self,
        *,
        deposition_id: int | str,
        file_id: str,
    ) -> dict[str, Any]:
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        return get_zenodo_deposition_file(
            deposition_id,
            file_id,
            base_url=self.url,
            headers=self.headers,
        )
