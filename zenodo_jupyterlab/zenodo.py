from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def is_zenodo_access_token_valid(access_token: str) -> bool:
    request = Request(
        "https://zenodo.org/api/deposit/depositions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status == 200
    except (HTTPError, URLError, TimeoutError):
        return False
