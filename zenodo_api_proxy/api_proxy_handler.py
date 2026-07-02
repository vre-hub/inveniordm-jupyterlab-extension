from __future__ import annotations

from http import HTTPStatus
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base_handler import BaseProxyHandler
from .helpers import is_hop_by_hop_header


class ApiProxyHandler(BaseProxyHandler):
    SUPPORTED_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")

    def get(self, path: str | None = None) -> None:
        self.forward(path)

    def post(self, path: str | None = None) -> None:
        self.forward(path)

    def put(self, path: str | None = None) -> None:
        self.forward(path)

    def patch(self, path: str | None = None) -> None:
        self.forward(path)

    def delete(self, path: str | None = None) -> None:
        self.forward(path)

    def forward(self, path: str | None) -> None:
        zenodo_user_id = self.current_zenodo_user_id()
        if zenodo_user_id is None:
            self.write_json(
                {"message": "Missing or expired proxy session"},
                HTTPStatus.UNAUTHORIZED,
            )
            return
        token = self.token_store.get_token(zenodo_user_id)
        if token is None:
            self.write_json(
                {"message": "Missing or expired Zenodo token"},
                HTTPStatus.UNAUTHORIZED,
            )
            return

        target_url = f"{self.config.zenodo_base_url}/api{path or ''}"
        if self.request.query:
            target_url = f"{target_url}?{self.request.query}"

        request = Request(
            target_url,
            data=self.request.body or None,
            headers=self.forward_request_headers(token.access_token),
            method=self.request.method,
        )

        try:
            with urlopen(request, timeout=30) as response:
                self.write_proxied_response(
                    response.status,
                    dict(response.headers.items()),
                    response.read(),
                )
        except HTTPError as error:
            self.write_proxied_response(
                error.code,
                dict(error.headers.items()),
                error.read(),
            )
        except URLError as error:
            self.write_json(
                {"message": f"Could not reach Zenodo: {error.reason}"},
                HTTPStatus.BAD_GATEWAY,
            )

    def forward_request_headers(self, access_token: str) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": self.request.headers.get("Accept", "application/json"),
            "Authorization": f"Bearer {access_token}",
        }
        content_type = self.request.headers.get("Content-Type")
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def write_proxied_response(
        self,
        status: int,
        headers: dict[str, str],
        body: bytes,
    ) -> None:
        self.set_status(status)
        for name, value in headers.items():
            if is_hop_by_hop_header(name):
                continue
            lower_name = name.lower()
            if lower_name in {"content-length", "server", "date", "set-cookie"}:
                continue
            if lower_name.startswith("access-control-"):
                continue
            self.set_header(name, value)
        self.finish(body)
