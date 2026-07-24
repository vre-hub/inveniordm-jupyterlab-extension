from unittest.mock import patch
from urllib.error import URLError

from tornado.testing import AsyncHTTPTestCase

from zenodo_api_proxy.app import create_app
from zenodo_api_proxy.config import Config
from zenodo_api_proxy.types import ProxyState
from zenodo_auth.token_store import MultiTokenStore, StoredToken


class _TokenStore(MultiTokenStore):
    def get_token(self, token_id: str) -> StoredToken | None:
        return StoredToken("secret", True) if token_id == "user" else None

    def set_token(
        self,
        token_id: str,
        access_token: str,
        access_token_valid: bool,
        sandbox: bool = False,
    ) -> None:
        raise NotImplementedError

    def remove_token(self, token_id: str) -> None:
        raise NotImplementedError


class _Response:
    def __init__(self, chunks: list[bytes], content_type: str):
        self.status = 200
        self.headers = {
            "Content-Length": str(sum(map(len, chunks))),
            "Content-Type": content_type,
        }
        self._chunks = iter(chunks)

    def read(self, size: int = -1) -> bytes:
        return next(self._chunks, b"")

    def getcode(self) -> int:
        return self.status

    def close(self) -> None:
        pass


class TestApiProxyHandler(AsyncHTTPTestCase):
    def get_app(self):
        return create_app(
            Config(zenodo_base_url="https://zenodo.example"),
            state=ProxyState(sessions={"session": "user"}),
            token_store=_TokenStore(),
        )

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Cookie": "zenodo_sandbox_proxy_session=session"}

    def test_streams_download_response_chunks(self):
        received = []
        response = _Response(
            [b"first chunk", b"second chunk"],
            "application/octet-stream",
        )

        with patch("zenodo_api_proxy.api_proxy_handler.urlopen", return_value=response):
            result = self.fetch(
                "/api/records/1/files/data/content",
                headers=self.auth_headers,
                streaming_callback=received.append,
            )

        assert result.code == 200
        assert b"".join(received) == b"first chunksecond chunk"
        assert result.headers["Content-Length"] == "23"

    def test_preserves_percent_encoded_file_path(self):
        upstream_urls = []

        def urlopen(request, timeout):
            upstream_urls.append(request.full_url)
            return _Response([b"file contents"], "application/pdf")

        with patch("zenodo_api_proxy.api_proxy_handler.urlopen", side_effect=urlopen):
            result = self.fetch(
                "/api/records/541036/draft/files/"
                "FINAL%20REPORT_Results%20%281%29.pdf?download=1",
                headers=self.auth_headers,
            )

        assert result.code == 200
        assert upstream_urls == [
            "https://zenodo.example/api/records/541036/draft/files/"
            "FINAL%20REPORT_Results%20%281%29.pdf?download=1"
        ]

    def test_streams_upload_request_body(self):
        received = []

        def urlopen(request, timeout):
            received.extend(request.data)
            return _Response([b"{}"], "application/json")

        with patch("zenodo_api_proxy.api_proxy_handler.urlopen", side_effect=urlopen):
            result = self.fetch(
                "/api/records/1/draft/files/data/content",
                method="PUT",
                headers=self.auth_headers,
                body=b"uploaded content",
            )

        assert result.code == 200
        assert b"".join(received) == b"uploaded content"

    def test_upstream_failure_does_not_block_incoming_upload(self):
        with patch(
            "zenodo_api_proxy.api_proxy_handler.urlopen",
            side_effect=URLError("unavailable"),
        ):
            result = self.fetch(
                "/api/records/1/draft/files/data/content",
                method="PUT",
                headers=self.auth_headers,
                body=b"x" * (1024 * 1024),
            )

        assert result.code == 502
