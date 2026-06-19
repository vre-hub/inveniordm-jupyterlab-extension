from typing import Any

import requests


ZENODO_SERVER_URL = "https://zenodo.org"
ZENODO_SANDBOX_SERVER_URL = "https://sandbox.zenodo.org"

def _headers(access_token: str | None) -> dict[str, str]:
    """
    Return the headers for a Zenodo API request,
    including the Authorization header if an access token is provided.
    """
    headers = {"Accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers

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


def list_zenodo_depositions(
    *,
    access_token: str | None,
    sandbox: bool = False,
    page: int = 1,
    size: int = 10,
) -> dict[str, Any]:
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
