"""
Wrapper for the raw Zenodo API requests, using the requests library.
TODO consider using httpx instead of requests, for async support.
"""

from collections.abc import Iterable
from typing import Any, Protocol
from urllib.parse import urlparse

import requests


ZENODO_SERVER_URL = "https://zenodo.org"
ZENODO_SANDBOX_SERVER_URL = "https://sandbox.zenodo.org"


class ZenodoFileResponse(Protocol):
    """
    Response object for a Zenodo file download
    """
    def iter_bytes(self, chunk_size: int) -> Iterable[bytes]:
        ...

    def close(self) -> None:
        ...


class _RequestsZenodoFileResponse:
    """
    Response object for a Zenodo file download using the requests library.
    """
    def __init__(self, response: requests.Response):
        self.response = response

    def iter_bytes(self, chunk_size: int) -> Iterable[bytes]:
        return self.response.iter_content(chunk_size=chunk_size)

    def close(self) -> None:
        self.response.close()

def _headers(access_token: str | None) -> dict[str, str]:
    """
    Return the headers for a Zenodo API request,
    including the Authorization header if an access token is provided.
    """
    headers = {"Accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _is_zenodo_url(url: str) -> bool:
    hostname = urlparse(url).hostname
    return hostname in {
        urlparse(ZENODO_SERVER_URL).hostname,
        urlparse(ZENODO_SANDBOX_SERVER_URL).hostname,
    }


def is_zenodo_access_token_valid(access_token: str, sandbox: bool = False) -> bool:
    """
    Perform a dummy API call to Zenodo using the provided access token to check if it's valid.
    """
    server_url = ZENODO_SANDBOX_SERVER_URL if sandbox else ZENODO_SERVER_URL
    try:
        response = requests.get(
            f"{server_url}/api/me",
            headers=_headers(access_token),
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
    access_token: str,
    sandbox: bool = False,
) -> dict[str, Any]:
    """
    Fetch the authenticated user's Zenodo profile and return the public fields
    needed by the JupyterLab frontend.
    """
    server_url = ZENODO_SANDBOX_SERVER_URL if sandbox else ZENODO_SERVER_URL
    response = requests.get(
        f"{server_url}/api/me",
        headers=_headers(access_token),
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
    access_token: str | None = None,
    sandbox: bool = False,
    page: int = 1,
    size: int = 10,
    sort: str = "bestmatch",
    all_versions: bool = False,
    filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Search published Zenodo records.
    """
    server_url = ZENODO_SANDBOX_SERVER_URL if sandbox else ZENODO_SERVER_URL
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
        f"{server_url}/api/records",
        params=params,
        headers=_headers(access_token),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_zenodo_files(
    files_url: str,
    *,
    access_token: str | None = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """
    Fetch files from a Zenodo files URL provided by a record or deposition.
    """
    response = requests.get(
        files_url,
        headers=_headers(access_token),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_zenodo_deposition_file(
    deposition_id: int | str,
    file_id: str,
    *,
    access_token: str | None = None,
    sandbox: bool = False,
) -> dict[str, Any]:
    """
    Fetch one file for a Zenodo deposition.
    """
    server_url = ZENODO_SANDBOX_SERVER_URL if sandbox else ZENODO_SERVER_URL
    response = requests.get(
        f"{server_url}/api/deposit/depositions/{deposition_id}/files/{file_id}",
        headers=_headers(access_token),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def open_zenodo_file(
    file_url: str,
    *,
    access_token: str | None = None,
) -> ZenodoFileResponse:
    """
    Open a streaming response for a Zenodo file URL.
    """
    if not _is_zenodo_url(file_url):
        raise ValueError("File URL must be a Zenodo URL")

    response = requests.get(
        file_url,
        headers=_headers(access_token),
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
    access_token: str | None,
    sandbox: bool = False,
    page: int = 1,
    size: int = 10,
) -> list[dict[str, Any]]:
    """
    List depositions owned by the authenticated user.
    """
    server_url = ZENODO_SANDBOX_SERVER_URL if sandbox else ZENODO_SERVER_URL
    response = requests.get(
        f"{server_url}/api/deposit/depositions",
        params={"page": page, "size": size},
        headers=_headers(access_token),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
