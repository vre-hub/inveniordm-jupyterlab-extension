from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Coroutine, Iterable
from queue import Full, Queue
from threading import Event
from typing import Any

import tornado.web

from .base_handler import BaseProxyHandler


class _RequestBody:
    """Pass incoming request chunks to a consumer without buffering the body."""

    def __init__(self) -> None:
        self._chunks: Queue[bytes | None] = Queue(maxsize=2)
        self._aborted = Event()

    async def write(self, chunk: bytes) -> None:
        while not self._aborted.is_set():
            try:
                self._chunks.put_nowait(chunk)
                return
            except Full:
                await asyncio.sleep(0.01)

    async def finish(self) -> None:
        while not self._aborted.is_set():
            try:
                self._chunks.put_nowait(None)
                return
            except Full:
                await asyncio.sleep(0.01)

    def abort(self) -> None:
        self._aborted.set()

    def __iter__(self):
        return self

    def __next__(self) -> bytes:
        if self._aborted.is_set():
            raise StopIteration
        chunk = self._chunks.get()
        if chunk is None:
            raise StopIteration
        return chunk


@tornado.web.stream_request_body
class StreamingRequestBodyHandler(BaseProxyHandler, ABC):
    """Tornado handler base that streams its request body to an async task."""

    def prepare(self) -> None:
        self._request_body: _RequestBody | None = None
        self._streaming_task: asyncio.Task[None] | None = None
        if self.request.method == "OPTIONS":
            return

        has_body = (
            int(self.request.headers.get("Content-Length", "0")) > 0
            or self.request.headers.get("Transfer-Encoding", "").lower() == "chunked"
        )
        self._request_body = _RequestBody() if has_body else None

        # Route arguments are percent-decoded by Tornado. Pass the original
        # encoded path so proxy handlers can forward it without reconstructing
        # or double-encoding it.
        path = self.request.path
        request = self.start_streaming_request(path)
        if request is None:
            self._abort_request_body()
            return

        self._streaming_task = asyncio.create_task(request)
        self._streaming_task.add_done_callback(lambda task: self._abort_request_body())

    @property
    def request_body(self) -> Iterable[bytes] | None:
        return self._request_body

    @abstractmethod
    def start_streaming_request(
        self,
        path: str,
    ) -> Coroutine[Any, Any, None] | None:
        """Start consuming the request body and producing the response."""

    async def data_received(self, chunk: bytes) -> None:
        if self._request_body is not None:
            await self._request_body.write(chunk)

    async def get(self, *args: str, **kwargs: str) -> None:
        await self._finish_streaming_request()

    async def post(self, *args: str, **kwargs: str) -> None:
        await self._finish_streaming_request()

    async def put(self, *args: str, **kwargs: str) -> None:
        await self._finish_streaming_request()

    async def patch(self, *args: str, **kwargs: str) -> None:
        await self._finish_streaming_request()

    async def delete(self, *args: str, **kwargs: str) -> None:
        await self._finish_streaming_request()

    async def _finish_streaming_request(self) -> None:
        if self._request_body is not None:
            await self._request_body.finish()
        if self._streaming_task is not None:
            await self._streaming_task

    def _abort_request_body(self) -> None:
        if self._request_body is not None:
            self._request_body.abort()

    def on_connection_close(self) -> None:
        self._abort_request_body()
        if self._streaming_task is not None:
            self._streaming_task.cancel()
