from dataclasses import dataclass
from typing import Any

from .token_store import TokenStore
from .zenodo_helpers import include_zenodo_files
from .zenodo import (
    ZenodoFileResponse,
    get_zenodo_deposition_file,
    get_zenodo_me,
    is_zenodo_access_token_valid,
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
    using a TokenStore to manage the access token.
    """
    def __init__(
        self,
        token_store: TokenStore,
        token_id: str,
        sandbox_override: bool | None = None,
    ):
        self.token_store = token_store
        self.token_id = token_id
        self.sandbox_override = sandbox_override

    @property
    def sandbox(self) -> bool:
        if self.sandbox_override is not None:
            return self.sandbox_override

        token = self.token_store.get_token(self.token_id)
        return token.sandbox if token is not None else False

    def get_access_token_status(self) -> AccessTokenStatus:
        token = self.token_store.get_token(self.token_id)
        return AccessTokenStatus(
            access_token_present=token is not None,
            access_token_valid=(
                token.access_token_valid
                if token is not None
                else False
            ),
            sandbox=token.sandbox if token is not None else False,
        )

    def set_access_token(
        self,
        access_token: str,
    ) -> bool:
        sandbox = False
        access_token_valid = False
        for candidate_sandbox in (False, True):
            if is_zenodo_access_token_valid(access_token, candidate_sandbox):
                sandbox = candidate_sandbox
                access_token_valid = True
                break

        if not access_token_valid:
            return False

        self.token_store.set_access_token(
            self.token_id, access_token, access_token_valid, sandbox
        )
        return True

    def remove_access_token(self) -> None:
        self.token_store.remove_access_token(self.token_id)

    def get_zenodo_me(self) -> dict[str, Any]:
        token = self.token_store.get_token(self.token_id)
        if token is None:
            raise ValueError("Missing Zenodo access token")

        return get_zenodo_me(
            access_token=token.access_token,
            sandbox=self.sandbox,
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
        token = self.token_store.get_token(self.token_id)

        records = search_zenodo_records(
            query,
            access_token=token.access_token if token is not None else None,
            sandbox=self.sandbox,
            page=page,
            size=size,
            sort=sort,
            all_versions=all_versions,
            filters=filters,
        )
        if include_files:
            include_zenodo_files(
                records.get("hits", {}).get("hits", []),
                access_token=token.access_token if token is not None else None,
            )

        return records

    def list_zenodo_depositions(
        self,
        *,
        page: int = 1,
        size: int = 10,
        include_files: bool = False,
    ) -> list[dict[str, Any]]:
        token = self.token_store.get_token(self.token_id)

        depositions = list_zenodo_depositions(
            access_token=token.access_token if token is not None else None,
            sandbox=self.sandbox,
            page=page,
            size=size,
        )
        if include_files:
            include_zenodo_files(
                depositions,
                access_token=token.access_token if token is not None else None,
            )

        return depositions

    def open_zenodo_file(
        self,
        *,
        file_url: str,
    ) -> ZenodoFileResponse:
        token = self.token_store.get_token(self.token_id)
        if token is None:
            raise ValueError("Missing Zenodo access token")

        return open_zenodo_file(
            file_url,
            access_token=token.access_token,
        )

    def get_zenodo_deposition_file(
        self,
        *,
        deposition_id: int | str,
        file_id: str,
    ) -> dict[str, Any]:
        token = self.token_store.get_token(self.token_id)
        if token is None:
            raise ValueError("Missing Zenodo access token")

        return get_zenodo_deposition_file(
            deposition_id,
            file_id,
            access_token=token.access_token,
            sandbox=self.sandbox,
        )
