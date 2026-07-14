from __future__ import annotations

import asyncio
from collections.abc import Coroutine, Iterable
from http import HTTPStatus
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .helpers import is_hop_by_hop_header
from .streaming_request_handler import StreamingRequestBodyHandler


class ApiProxyHandler(StreamingRequestBodyHandler):
    SUPPORTED_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")

    def start_streaming_request(
        self,
        path: str | None = None,
    ) -> Coroutine[Any, Any, None] | None:
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

        return self.forward(
            path,
            token.access_token,
            request_body=self.request_body,
        )

    async def forward(
        self,
        path: str | None,
        access_token: str,
        *,
        request_body: Iterable[bytes] | None,
    ) -> None:
        target_url = f"{self.config.zenodo_base_url}/api{path or ''}"
        if self.request.query:
            target_url = f"{target_url}?{self.request.query}"

        request = Request(
            target_url,
            data=request_body,
            headers=self.forward_request_headers(access_token),
            method=self.request.method,
        )

        try:
            response = await asyncio.to_thread(urlopen, request, timeout=30)
        except HTTPError as error:
            response = error
        except URLError as error:
            self.write_json(
                {"message": f"Could not reach Zenodo: {error.reason}"},
                HTTPStatus.BAD_GATEWAY,
            )
            return

        try:
            status = response.getcode()
            if not isinstance(status, int):
                raise ValueError("Upstream response is missing an HTTP status")
            self.write_proxied_response_headers(
                status,
                dict(response.headers.items()),
            )
            while True:
                chunk = await asyncio.to_thread(response.read, 1024 * 1024)
                if not chunk:
                    break
                self.write(chunk)
                await self.flush()
            self.finish()
        finally:
            response.close()

    def forward_request_headers(self, access_token: str) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": self.request.headers.get("Accept", "application/json"),
            "Authorization": f"Bearer {access_token}",
        }
        for name in ("Content-Type", "Content-Length"):
            value = self.request.headers.get(name)
            if value:
                headers[name] = value
        return headers

    def write_proxied_response_headers(
        self,
        status: int,
        headers: dict[str, str],
    ) -> None:
        self.set_status(status)
        for name, value in headers.items():
            if is_hop_by_hop_header(name):
                continue
            lower_name = name.lower()
            if lower_name in {"server", "date", "set-cookie"}:
                continue
            if lower_name.startswith("access-control-"):
                continue
            self.set_header(name, value)
