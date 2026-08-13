from http.cookies import SimpleCookie
from types import SimpleNamespace

import pytest

from inveniordm_auth.remote_servers import (
    RemoteServerRegistry,
    UnknownRemoteServerError,
)
from inveniordm_jupyterlab.inveniordm_requests import proxy_inveniordm_requests_factory
from inveniordm_jupyterlab.inveniordm_requests.proxy_inveniordm_requests_factory import (
    ProxyInvenioRDMRequestsFactory,
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
            "inveniordm_user_id": 123,
        }


def test_proxy_factory_passes_cached_inveniordm_user_id(monkeypatch):
    remote_servers = RemoteServerRegistry(
        {
            "zenodo_sandbox": {
                "label": "Zenodo Sandbox",
                "base_url": "https://sandbox.zenodo.org",
                "oauth_client_id": "client-id",
                "proxy_url": "http://127.0.0.1:8001",
                "proxy_session_cookie_name": "zenodo_sandbox_proxy_session",
            }
        }
    )
    cookies = SimpleCookie()
    cookies["zenodo_sandbox_proxy_session"] = "session"
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return _Response()

    monkeypatch.setattr(proxy_inveniordm_requests_factory.requests, "get", get)
    factory = ProxyInvenioRDMRequestsFactory(remote_servers)
    handler = _Handler(cookies)

    first = factory.create_inveniordm_requests(handler)
    second = factory.create_inveniordm_requests(handler)

    assert first.inveniordm_user_id == "123"
    assert second.inveniordm_user_id == "123"
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
    factory = ProxyInvenioRDMRequestsFactory(remote_servers)
    handler = _Handler(SimpleCookie(), remote_server="removed-server")

    with pytest.raises(UnknownRemoteServerError) as raised:
        factory.create_inveniordm_requests(handler)

    assert raised.value.remote_server_id == "removed-server"


def test_proxy_factory_uses_default_instead_of_authenticated_server():
    remote_servers = RemoteServerRegistry(
        {
            "default": {
                "label": "Default",
                "base_url": "https://default.example",
                "proxy_url": "http://default-proxy.example",
                "proxy_session_cookie_name": "default_session",
            },
            "connected": {
                "label": "Connected",
                "base_url": "https://connected.example",
                "proxy_url": "http://connected-proxy.example",
                "proxy_session_cookie_name": "connected_session",
            },
        },
        default_server_id="default",
    )
    cookies = SimpleCookie()
    cookies["connected_session"] = "session"

    requests = ProxyInvenioRDMRequestsFactory(
        remote_servers
    ).create_inveniordm_requests(_Handler(cookies))

    assert requests.url == "https://default.example"
    assert requests.headers == {}
    assert requests.inveniordm_user_id is None
