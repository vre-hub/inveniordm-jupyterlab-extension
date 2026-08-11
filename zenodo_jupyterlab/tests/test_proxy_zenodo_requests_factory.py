from http.cookies import SimpleCookie
from types import SimpleNamespace

import pytest

from zenodo_auth.remote_servers import UnknownRemoteServerError
from zenodo_jupyterlab.zenodo_requests import proxy_zenodo_requests_factory
from zenodo_jupyterlab.zenodo_requests.proxy_zenodo_requests_factory import (
    ProxyZenodoRequestsFactory,
)


class _Handler:
    def __init__(self, cookies, remote_server=None):
        self.request = SimpleNamespace(cookies=cookies)
        self.remote_server = remote_server

    def get_query_argument(self, name, default=None):
        return self.remote_server if name == "remote_server" else default


class _Response:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "authenticated": True,
            "zenodo_user_id": 123,
        }


def test_proxy_factory_passes_cached_zenodo_user_id(monkeypatch, remote_servers):
    cookies = SimpleCookie()
    cookies["zenodo_sandbox_proxy_session"] = "session"
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return _Response()

    monkeypatch.setattr(proxy_zenodo_requests_factory.requests, "get", get)
    factory = ProxyZenodoRequestsFactory(remote_servers)
    handler = _Handler(cookies)

    first = factory.create_zenodo_requests(handler)
    second = factory.create_zenodo_requests(handler)

    assert first.zenodo_user_id == "123"
    assert second.zenodo_user_id == "123"
    assert calls == [
        (
            "http://127.0.0.1:8001/auth/status",
            {
                "headers": {"Cookie": "zenodo_sandbox_proxy_session=session"},
                "timeout": 5,
            },
        )
    ]


def test_proxy_factory_rejects_unknown_remote_server_override(remote_servers):
    factory = ProxyZenodoRequestsFactory(remote_servers)
    handler = _Handler(SimpleCookie(), remote_server="removed-server")

    with pytest.raises(UnknownRemoteServerError) as raised:
        factory.create_zenodo_requests(handler)

    assert raised.value.remote_server_id == "removed-server"
