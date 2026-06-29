from dataclasses import dataclass
from typing import Any

from .zenodo_helpers import include_zenodo_files
from .zenodo import (
    ZenodoFileResponse,
    get_zenodo_deposition_file,
    get_zenodo_me,
    list_zenodo_depositions,
    open_zenodo_file,
    search_zenodo_records,
)


@dataclass
class AccessTokenStatus:
    access_token_present: bool
    access_token_valid: bool
    sandbox: bool


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
