from functools import lru_cache
from http.cookies import SimpleCookie

import requests
from jupyter_server.base.handlers import APIHandler

from inveniordm_auth.remote_servers import RemoteServerId, RemoteServerRegistry

from ..inveniordm_auth.auth_controller import InvenioRDMAuthController
from ..inveniordm_auth.proxy_auth_controller import ProxyInvenioRDMAuthController
from .inveniordm_requests import InvenioRDMRequests
from .inveniordm_requests_factory import (
    InvenioRDMRequestsFactory,
    get_remote_server_override,
)


def _cookie_header(cookie_name: str, cookie_value: str) -> dict[str, str]:
    cookie = SimpleCookie()
    cookie[cookie_name] = cookie_value
    return {"Cookie": cookie.output(header="", sep=";").strip()}


def _nonempty_cookie(cookie):
    if cookie is None or not cookie.value:
        return None

    return cookie


class ProxyInvenioRDMRequestsFactory(InvenioRDMRequestsFactory):
    def __init__(self, remote_servers: RemoteServerRegistry):
        super().__init__(remote_servers)
        self._auth_controller = ProxyInvenioRDMAuthController(
            self._proxy_url,
            remote_servers.default.id,
        )

    @property
    def auth_controller(self) -> InvenioRDMAuthController:
        return self._auth_controller

    def create_inveniordm_requests(self, handler: APIHandler) -> InvenioRDMRequests:
        remote_server_override = get_remote_server_override(handler)
        cookies = {
            server.id: _nonempty_cookie(
                handler.request.cookies.get(server.proxy_session_cookie_name)
            )
            for server in self.remote_servers.all()
        }

        if remote_server_override is not None:
            return self._create_requests_for_server(
                remote_server_override, cookies.get(remote_server_override)
            )

        for server in self.remote_servers.all():
            if cookies[server.id] is not None:
                return self._create_requests_for_server(
                    server.id,
                    cookies[server.id],
                )

        return InvenioRDMRequests(url=self.remote_servers.default.base_url)

    def _create_requests_for_server(
        self,
        remote_server_id: RemoteServerId,
        proxy_session,
    ) -> InvenioRDMRequests:
        server = self.remote_servers.get(remote_server_id)
        if proxy_session is None:
            return InvenioRDMRequests(url=server.base_url)

        return InvenioRDMRequests(
            url=server.proxy_url,
            headers=_cookie_header(
                server.proxy_session_cookie_name,
                proxy_session.value,
            ),
            inveniordm_user_id=self._get_inveniordm_user_id(
                remote_server_id,
                proxy_session.value,
            ),
        )

    @lru_cache(maxsize=128)
    def _get_inveniordm_user_id(
        self,
        remote_server_id: RemoteServerId,
        proxy_session: str,
    ) -> str | None:
        response = requests.get(
            f"{self._proxy_url(remote_server_id)}/auth/status",
            headers=_cookie_header(
                self.remote_servers.get(remote_server_id).proxy_session_cookie_name,
                proxy_session,
            ),
            timeout=5,
        )
        response.raise_for_status()
        status = response.json()
        if not status.get("authenticated"):
            return None

        inveniordm_user_id = status.get("inveniordm_user_id")
        return str(inveniordm_user_id) if inveniordm_user_id is not None else None

    def _proxy_url(self, remote_server_id: RemoteServerId) -> str:
        return self.remote_servers.get(remote_server_id).proxy_url
