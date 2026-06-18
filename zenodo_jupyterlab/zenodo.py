from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ZENODO_SERVER_URL = "https://zenodo.org"
ZENODO_SANDBOX_SERVER_URL = "https://sandbox.zenodo.org"


def is_zenodo_access_token_valid(access_token: str, sandbox: bool = False) -> bool:
    """
    Perform a dummy API call to Zenodo using the provided access token to check if it's valid.
    """
    server_url = ZENODO_SANDBOX_SERVER_URL if sandbox else ZENODO_SERVER_URL
    request = Request(
        f"{server_url}/api/deposit/depositions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status == 200
    except (HTTPError, URLError, TimeoutError):
        return False
