from http.cookies import SimpleCookie
from types import SimpleNamespace

from zenodo_jupyterlab.zenodo_requests import proxy_zenodo_requests_factory
from zenodo_jupyterlab.zenodo_requests.proxy_zenodo_requests_factory import (
    ProxyZenodoRequestsFactory,
)


class _Handler:
    def __init__(self, cookies):
        self.request = SimpleNamespace(cookies=cookies)

    def get_query_argument(self, name, default=None):
        return default


class _Response:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "authenticated": True,
            "zenodo_user_id": 123,
        }


def test_proxy_factory_passes_cached_zenodo_user_id(monkeypatch):
    cookies = SimpleCookie()
    cookies["zenodo_sandbox_proxy_session"] = "session"
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return _Response()

    monkeypatch.setattr(proxy_zenodo_requests_factory.requests, "get", get)
    factory = ProxyZenodoRequestsFactory()
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
