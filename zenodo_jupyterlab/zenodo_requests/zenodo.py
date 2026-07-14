"""
Wrapper for the raw Zenodo API requests, using the requests library.
TODO consider using httpx instead of requests, for async support.
"""

from collections.abc import Iterable
from typing import Any, Protocol
from urllib.parse import quote, urljoin, urlparse, urlunparse

import requests


class ZenodoFileResponse(Protocol):
    """
    Response object for a Zenodo file download
    """
    @property
    def content_length(self) -> int | None:
        ...

    def iter_bytes(self, chunk_size: int) -> Iterable[bytes]:
        ...

    def close(self) -> None:
        ...


class BinaryReader(Protocol):
    def read(self, size: int = -1, /) -> bytes:
        ...


class _RequestsZenodoFileResponse:
    """
    Response object for a Zenodo file download using the requests library.
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


def _headers(headers: dict[str, str] | None = None) -> dict[str, str]:
    """
    Return headers for a Zenodo API request, with defaults applied.
    """
    return {"Accept": "application/json", **(headers or {})}


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _rebase_zenodo_url(url: str, *, base_url: str) -> str:
    """
    Rebase absolute API links onto the configured Zenodo server URL.
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


def _is_api_url(url: str) -> bool:
    return urlparse(url).path.startswith("/api/")


def is_zenodo_request_authenticated(
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
        return False # never reached
    except requests.RequestException:
        return False


def get_zenodo_me(
    *,
    base_url: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    """
    Fetch the authenticated user's Zenodo profile and return the public fields
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


def search_zenodo_records(
    query: str,
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
    page: int = 1,
    size: int = 10,
    sort: str = "bestmatch",
    all_versions: bool = False,
    filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Search published Zenodo records.
    """
    params: dict[str, Any] = {
        "q": query,
        "page": page,
        "size": size,
        "sort": sort,
        "all_versions": all_versions,
    }
    if filters:
        params.update(filters)

    response = requests.get(
        f"{_normalize_base_url(base_url)}/api/records",
        params=params,
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_zenodo_files(
    files_url: str,
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """
    Fetch files from a Zenodo files URL provided by a record or deposition.
    """
    response = requests.get(
        _rebase_zenodo_url(files_url, base_url=base_url),
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_zenodo_deposition_file(
    deposition_id: int | str,
    file_id: str,
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Fetch one file for a Zenodo deposition.
    Works for files in both draft and published depositions.
    """
    record_id = quote(str(deposition_id), safe="")
    filename = quote(file_id, safe="")
    response = requests.get(
        (
            f"{_normalize_base_url(base_url)}/api/records/{record_id}"
            f"/draft/files/{filename}"
        ),
        headers=_headers(headers),
        timeout=10,
    )

    # If the file is not in the draft, try the published version.
    if response.status_code == 404:
        response = requests.get(
            f"{_normalize_base_url(base_url)}/api/records/{record_id}/files/{filename}",
            headers=_headers(headers),
            timeout=10,
        )
    response.raise_for_status()
    return response.json()


def open_zenodo_file(
    file_url: str,
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
) -> ZenodoFileResponse:
    """
    Open a streaming response for a Zenodo file URL.
    """
    if not _is_api_url(file_url):
        raise ValueError("File URL must be an API URL")

    response = requests.get(
        _rebase_zenodo_url(file_url, base_url=base_url),
        headers=_headers(headers),
        stream=True,
        timeout=30,
    )
    try:
        response.raise_for_status()
    except requests.RequestException:
        response.close()
        raise
    return _RequestsZenodoFileResponse(response)


def list_zenodo_depositions(
    *,
    base_url: str,
    headers: dict[str, str] | None,
    page: int = 1,
    size: int = 10,
) -> list[dict[str, Any]]:
    """
    List depositions owned by the authenticated user.
    """
    response = requests.get(
        f"{_normalize_base_url(base_url)}/api/user/records",
        params={"page": page, "size": size},
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("hits", {}).get("hits", [])


def get_zenodo_deposition(
    deposition_id: int | str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> dict[str, Any]:
    """
    Fetch a deposition owned by the authenticated user.
    """
    response = requests.get(
        f"{_normalize_base_url(base_url)}/api/user/records",
        params={"q": f"id:{deposition_id}", "size": 10},
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()
    hits = response.json().get("hits", {}).get("hits", [])
    deposition = next(
        (item for item in hits if str(item.get("id")) == str(deposition_id)),
        None,
    )
    if deposition is None:
        raise ValueError(f"Deposition not found: {deposition_id}")
    return deposition


def get_zenodo_deposition_at_url(
    deposition_url: str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> dict[str, Any]:
    """
    Fetch a deposition using a link returned by the Zenodo API.
    """
    response = requests.get(
        _rebase_zenodo_url(deposition_url, base_url=base_url),
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def create_zenodo_deposition_version(
    deposition_id: int | str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> dict[str, Any]:
    """
    Create or return the editable latest draft for a published deposition.
    """
    response = requests.post(
        (
            f"{_normalize_base_url(base_url)}/api/records/"
            f"{quote(str(deposition_id), safe='')}/versions"
        ),
        headers=_headers(headers),
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
    return draft


def create_zenodo_deposition(
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> dict[str, Any]:
    """
    Create an empty Zenodo deposition draft.
    """
    response = requests.post(
        f"{_normalize_base_url(base_url)}/api/records",
        json={"files": {"enabled": True}},
        headers=_headers({"Content-Type": "application/json", **(headers or {})}),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def upload_zenodo_deposition_file(
    bucket_url: str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
    filename: str,
    content: bytes | BinaryReader,
) -> dict[str, Any]:
    """
    Initialize, upload, and commit one InvenioRDM draft file.
    """

    # Initialize the file in the draft's file collection
    # which returns the content and commit links for the file upload.
    files_url = _rebase_zenodo_url(bucket_url, base_url=base_url)
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
        _rebase_zenodo_url(content_url, base_url=base_url),
        data=content,
        headers=_headers(
            {"Content-Type": "application/octet-stream", **(headers or {})}
        ),
        timeout=30,
    )
    response.raise_for_status()

    # Commit the file to finalize the upload and make it available in the draft.
    commit_response = requests.post(
        _rebase_zenodo_url(commit_url, base_url=base_url),
        headers=_headers(headers),
        timeout=10,
    )
    commit_response.raise_for_status()
    return commit_response.json()


def delete_zenodo_deposition_file(
    bucket_url: str,
    *,
    base_url: str,
    headers: dict[str, str] | None,
    file_key: str,
) -> None:
    """
    Delete one file from an InvenioRDM draft by its object key.
    """
    delete_url = f"{bucket_url.rstrip('/')}/{quote(file_key, safe='')}"
    response = requests.delete(
        _rebase_zenodo_url(delete_url, base_url=base_url),
        headers=_headers(headers),
        timeout=10,
    )
    response.raise_for_status()
