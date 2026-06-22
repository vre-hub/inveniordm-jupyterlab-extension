from dataclasses import dataclass
from typing import Any

from .token_store import TokenStore
from .zenodo import (
    get_zenodo_me,
    is_zenodo_access_token_valid,
    list_zenodo_depositions,
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
    def __init__(self, token_store: TokenStore, token_id: str):
        self.token_store = token_store
        self.token_id = token_id

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
        sandbox: bool,
    ) -> bool:
        access_token_valid = is_zenodo_access_token_valid(access_token, sandbox)
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
            sandbox=token.sandbox,
        )

    def search_zenodo_records(
        self,
        *,
        query: str,
        sandbox_override: bool | None = None,
        page: int = 1,
        size: int = 10,
        sort: str = "bestmatch",
        all_versions: bool = False,
        filters: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        token = self.token_store.get_token(self.token_id)
        sandbox = (
            sandbox_override
            if sandbox_override is not None
            else token.sandbox if token is not None else False
        )

        return search_zenodo_records(
            query,
            access_token=token.access_token if token is not None else None,
            sandbox=sandbox,
            page=page,
            size=size,
            sort=sort,
            all_versions=all_versions,
            filters=filters,
        )

    def list_zenodo_depositions(
        self,
        *,
        sandbox_override: bool | None = None,
        page: int = 1,
        size: int = 10,
    ) -> dict[str, Any]:
        token = self.token_store.get_token(self.token_id)
        sandbox = (
            sandbox_override
            if sandbox_override is not None
            else token.sandbox if token is not None else False
        )

        return list_zenodo_depositions(
            access_token=token.access_token if token is not None else None,
            sandbox=sandbox,
            page=page,
            size=size,
        )
