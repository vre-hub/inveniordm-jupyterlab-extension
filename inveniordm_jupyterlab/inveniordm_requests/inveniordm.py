"""
Wrapper for the raw InvenioRDM API requests, using the requests library.
TODO consider using httpx instead of requests, for async support.
"""

import base64
from collections.abc import Iterable
from typing import Any, Literal, Protocol, TypedDict
from urllib.parse import quote, urljoin, urlparse, urlunparse

import requests

from ..inveniordm_file_identifier import InvenioRDMFileIdentifier
from ..inveniordm_record_identifier import InvenioRDMRecordStatus

InvenioRDMPermission = Literal[
    "manage", "edit", "preview", "view"
]  # "preview" means "preview drafts", "view" means "view restricted files"


class InvenioRDMRecordSearchHits(TypedDict, total=False):
    hits: list[dict[str, Any]]
    total: int


class InvenioRDMRecordSearchResponse(TypedDict, total=False):
    hits: InvenioRDMRecordSearchHits
    links: dict[str, Any]


class InvenioRDMFileResponse(Protocol):
    """
    Response object for a InvenioRDM file download
    """

    @property
    def content_length(self) -> int | None: ...

    def iter_bytes(self, chunk_size: int) -> Iterable[bytes]: ...

    def close(self) -> None: ...


class BinaryReader(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...


class _RequestsInvenioRDMFileResponse:
    """
    Response object for a InvenioRDM file download using the requests library.
    """

    def __init__(self, response: requests.Response):
        self.response = response

    @property
    def content_length(self) -> int | None:
        value = self.response.headers.get("Content-Length")
        return int(value) if value else None

    def iter_bytes(self, chunk_size: int) -> Iterable[bytes]:
        return self.response.iter_content(chunk_size=chunk_size)

    def close(self) -> None:
        self.response.close()


def _headers(
    headers: dict[str, str] | None = None,
    *,
    accept_invenio: bool = False,
) -> dict[str, str]:
    """
    Return headers for a InvenioRDM API request, with defaults applied.
    """
    accept = (
        "application/vnd.inveniordm.v1+json" if accept_invenio else "application/json"
    )
    return {"Accept": accept, **(headers or {})}


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _rebase_inveniordm_url(url: str, *, base_url: str) -> str:
    """
    Rebase absolute API links onto the configured InvenioRDM server URL.
    """
    parsed_url = urlparse(urljoin(f"{_normalize_base_url(base_url)}/", url))
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("URL must be absolute")
    if not parsed_url.path.startswith("/api/"):
        raise ValueError("URL must be an API URL")

    target_base = urlparse(_normalize_base_url(base_url))
    return urlunparse(
        (
            target_base.scheme,
            target_base.netloc,
            parsed_url.path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )


def check_inveniordm_authentication(
    *,
    base_url: str,
    headers: dict[str, str],
) -> bool:
    """
    Perform a dummy authenticated API call.
    """
    try:
        response = requests.get(
            f"{_normalize_base_url(base_url)}/api/me",
            headers=_headers(headers),
            timeout=5,
        )
        if response.status_code == 200:
            return True
        if response.status_code == 401:
            return False
        response.raise_for_status()
        return False  # never reached
    except requests.RequestException:
        return False


def get_inveniordm_me(
    *,
    base_url: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    """
    Fetch the authenticated user's InvenioRDM profile and return the public fields
    needed by the JupyterLab frontend.
    """
    response = requests.get(
        f"{_normalize_base_url(base_url)}/api/me",
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "email": data["email"],
        "id": data["id"],
    }


def search_inveniordm_records(
    query: str,
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
    page: int = 1,
    size: int = 10,
    sort: str = "bestmatch",
    allversions: bool = False,
) -> InvenioRDMRecordSearchResponse:
    """
    Search published InvenioRDM records.
    """
    params: dict[str, Any] = {
        "q": query,
        "page": page,
        "size": size,
        "sort": sort,
        "allversions": allversions,
    }

    response = requests.get(
        f"{_normalize_base_url(base_url)}/api/records",
        params=params,
        headers=_headers(headers, accept_invenio=True),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def list_inveniordm_record_files(
    files_url: str,
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Fetch a record's file collection using its InvenioRDM ``links.files`` URL.
    """
    response = requests.get(
        _rebase_inveniordm_url(files_url, base_url=base_url),
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def open_inveniordm_file(
    file_id: InvenioRDMFileIdentifier,
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
) -> InvenioRDMFileResponse:
    """
    Open a streaming response for a draft or published InvenioRDM file.
    """
    record_id = quote(str(file_id.record_id), safe="")
    filename = quote(file_id.file_key, safe="")
    variant_path = "draft/files" if file_id.record_status == "draft" else "files"
    file_url = (
        f"{_normalize_base_url(base_url)}/api/records/{record_id}/"
        f"{variant_path}/{filename}/content"
    )

    response = requests.get(
        file_url,
        headers=_headers(headers),
        stream=True,
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.RequestException:
        response.close()
        raise
    return _RequestsInvenioRDMFileResponse(response)


def list_inveniordm_user_records(
    *,
    base_url: str,
    headers: dict[str, str] | None,
    page: int = 1,
    size: int = 10,
    query: str | None = None,
    allversions: bool | None = None,
) -> InvenioRDMRecordSearchResponse:
    """
    List records owned by the authenticated user.
    """
    params: dict[str, Any] = {"page": page, "size": size}
    if query is not None:
        params["q"] = query
    if allversions is not None:
        params["allversions"] = allversions

    response = requests.get(
        f"{_normalize_base_url(base_url)}/api/user/records",
        params=params,
        headers=_headers(headers, accept_invenio=True),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def list_inveniordm_record_versions(
    record_id: int | str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> dict[str, Any]:
    """List all published versions belonging to a record."""
    response = requests.get(
        (
            f"{_normalize_base_url(base_url)}/api/records/"
            f"{quote(str(record_id), safe='')}/versions"
        ),
        headers=_headers(headers, accept_invenio=True),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_inveniordm_record_public_or_draft(
    record_id: int | str,
    *,
    record_status: InvenioRDMRecordStatus,
    base_url: str,
    headers: dict[str, str] | None,
) -> dict[str, Any]:
    """Fetch a draft or published record directly from the records API."""
    variant_path = "/draft" if record_status == "draft" else ""
    response = requests.get(
        (
            f"{_normalize_base_url(base_url)}/api/records/"
            f"{quote(str(record_id), safe='')}{variant_path}"
        ),
        headers=_headers(headers, accept_invenio=True),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def create_inveniordm_record_version(
    record_id: int | str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> dict[str, Any]:
    """
    Create a new draft version from a published record and import its files.
    """
    response = requests.post(
        (
            f"{_normalize_base_url(base_url)}/api/records/"
            f"{quote(str(record_id), safe='')}/versions"
        ),
        headers=_headers(headers, accept_invenio=True),
        timeout=10,
    )
    response.raise_for_status()
    draft = response.json()

    # InvenioRDM creates a file-empty new version. Import the previous
    # version's files to preserve the existing file-editing workflow.
    draft_id = quote(str(draft["id"]), safe="")
    import_response = requests.post(
        (
            f"{_normalize_base_url(base_url)}/api/records/{draft_id}"
            "/draft/actions/files-import"
        ),
        headers=_headers(headers),
        timeout=10,
    )
    import_response.raise_for_status()
    draft["files"] = import_response.json()
    return draft


def delete_inveniordm_record_draft(
    record_id: int | str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> None:
    """Delete/discard an InvenioRDM record draft."""
    response = requests.delete(
        (
            f"{_normalize_base_url(base_url)}/api/records/"
            f"{quote(str(record_id), safe='')}/draft"
        ),
        headers=_headers(headers, accept_invenio=True),
        timeout=10,
    )
    response.raise_for_status()


def create_inveniordm_record_draft(
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> dict[str, Any]:
    """
    Create an empty InvenioRDM record draft.
    """
    response = requests.post(
        f"{_normalize_base_url(base_url)}/api/records",
        json={"files": {"enabled": True}},
        headers=_headers(
            {"Content-Type": "application/json", **(headers or {})},
            accept_invenio=True,
        ),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def upload_inveniordm_draft_file(
    record_id: int | str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
    filename: str,
    content: bytes | BinaryReader,
) -> dict[str, Any]:
    """
    Initialize, upload, and commit one InvenioRDM draft file by record ID.
    """

    # Initialize the file in the draft's file collection
    # which returns the content and commit links for the file upload.
    encoded_record_id = quote(str(record_id), safe="")
    files_url = (
        f"{_normalize_base_url(base_url)}/api/records/{encoded_record_id}/draft/files"
    )
    initialize_response = requests.post(
        files_url,
        json=[{"key": filename}],
        headers=_headers({"Content-Type": "application/json", **(headers or {})}),
        timeout=10,
    )
    initialize_response.raise_for_status()
    entries = initialize_response.json().get("entries", [])
    entry = next((entry for entry in entries if entry.get("key") == filename), None)
    if entry is None:
        raise ValueError(f"Initialized file is missing from response: {filename}")

    content_url = entry.get("links", {}).get("content")
    commit_url = entry.get("links", {}).get("commit")
    if not content_url or not commit_url:
        raise ValueError(f"Initialized file has incomplete links: {filename}")

    # Upload the file content to the draft's file collection
    response = requests.put(
        _rebase_inveniordm_url(content_url, base_url=base_url),
        data=content,
        headers=_headers(
            {"Content-Type": "application/octet-stream", **(headers or {})}
        ),
        timeout=30,
    )
    response.raise_for_status()

    # Commit the file to finalize the upload and make it available in the draft.
    commit_response = requests.post(
        _rebase_inveniordm_url(commit_url, base_url=base_url),
        headers=_headers(headers),
        timeout=10,
    )
    commit_response.raise_for_status()
    return commit_response.json()


def delete_inveniordm_draft_file(
    record_id: int | str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
    file_key: str,
) -> None:
    """
    Delete one file from an InvenioRDM draft by record ID and object key.
    """
    encoded_record_id = quote(str(record_id), safe="")
    encoded_file_key = quote(file_key, safe="")
    delete_url = (
        f"{_normalize_base_url(base_url)}/api/records/{encoded_record_id}"
        f"/draft/files/{encoded_file_key}"
    )
    response = requests.delete(
        delete_url,
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()


def check_user_record_permission_workaround(
    record_id: int | str,
    user_id: int | str,
    permission_to_check: InvenioRDMPermission,
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> bool:
    """
    Check if a user has a specific permission on a record.
    Do this by querying /api/user/records?q=id:<record_id> AND parent.access.grant_tokens:<base64(subject_type).base64(subject_id).base64(permission)>
    """
    subject_type = "user"
    encoded_subject_type = base64.b64encode(subject_type.encode()).decode()
    encoded_user_id = base64.b64encode(str(user_id).encode()).decode()
    encoded_permission = base64.b64encode(permission_to_check.encode()).decode()
    encoded_grant_token = (
        f"{encoded_subject_type}.{encoded_user_id}.{encoded_permission}"
    )
    query = f"id:{record_id} AND parent.access.grant_tokens:{encoded_grant_token}"
    response = list_inveniordm_user_records(
        base_url=base_url,
        headers=headers,
        query=query,
        page=1,
        size=1,
    )
    has_permission = len(response.get("hits", {}).get("hits", [])) > 0
    return has_permission
