from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ZENODO_SERVER_URL = "https://zenodo.org"


def is_zenodo_access_token_valid(access_token: str) -> bool:
    # TODO instead of having this call everywhere, update the validity using the returns from other Zenodo Calls while the user is using the extension.
    request = Request(
        f"{ZENODO_SERVER_URL}/api/deposit/depositions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status == 200
    except (HTTPError, URLError, TimeoutError):
        return False
