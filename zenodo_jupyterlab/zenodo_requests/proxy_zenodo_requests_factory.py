import os
from http.cookies import SimpleCookie
from urllib.parse import urlencode

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join

from .zenodo_requests import ZenodoRequests
from .zenodo_requests_factory import (
    ZenodoRequestsFactory,
    get_sandbox_override,
)


def _cookie_header(cookie_name: str, cookie_value: str) -> dict[str, str]:
    cookie = SimpleCookie()
    cookie[cookie_name] = cookie_value
    return {"Cookie": cookie.output(header="", sep=";").strip()}


def _nonempty_cookie(cookie):
    if cookie is None or not cookie.value:
        return None

    return cookie


class ProxyZenodoRequestsFactory(ZenodoRequestsFactory):
    production_url = "https://zenodo.org"
    sandbox_url = "https://sandbox.zenodo.org"
    sandbox_proxy_session_cookie_name = os.environ.get(
        "ZENODO_SANDBOX_PROXY_SESSION_COOKIE_NAME",
        "zenodo_sandbox_proxy_session",
    )
    sandbox_proxy_public_url = "http://127.0.0.1:8001"
    production_proxy_session_cookie_name = os.environ.get(
        "ZENODO_PRODUCTION_PROXY_SESSION_COOKIE_NAME",
        "zenodo_production_proxy_session",
    )
    production_proxy_public_url = "http://127.0.0.1:8003"

    def create_zenodo_requests(self, handler: APIHandler) -> ZenodoRequests:
        sandbox_override = get_sandbox_override(handler)
        sandbox_cookie = _nonempty_cookie(
            handler.request.cookies.get(self.sandbox_proxy_session_cookie_name)
        )
        production_cookie = _nonempty_cookie(
            handler.request.cookies.get(self.production_proxy_session_cookie_name)
        )

        if sandbox_override is not None:
            cookie = sandbox_cookie if sandbox_override else production_cookie
            print(
                "Creating ZenodoRequests for "
                f"sandbox_override={sandbox_override}, cookie={cookie}"
            )
            return self._create_requests_for_server(sandbox_override, cookie)

        if sandbox_cookie is not None and production_cookie is None:
            print(f"Creating ZenodoRequests for sandbox=True, cookie={sandbox_cookie}")
            return self._create_requests_for_server(True, sandbox_cookie)

        if production_cookie is not None:
            print(
                "Creating ZenodoRequests for "
                f"sandbox=False, cookie={production_cookie}"
            )
            return self._create_requests_for_server(False, production_cookie)

        print(
            "Creating ZenodoRequests for "
            f"production_url={self.production_url} with no cookies"
        )
        return ZenodoRequests(url=self.production_url)

    def is_sandbox(self, zenodo_requests: ZenodoRequests) -> bool:
        return zenodo_requests.url in {
            self.sandbox_url,
            self.sandbox_proxy_public_url,
        }

    def handle_auth(self, handler: APIHandler, action: str) -> None:
        sandbox_override = get_sandbox_override(handler)
        sandbox = sandbox_override if sandbox_override is not None else False
        return_to = handler.get_query_argument("return_to", None)
        if return_to is None:
            return_to = handler.request.headers.get(
                "Referer",
                (
                    f"{handler.request.protocol}://{handler.request.host}"
                    f"{url_path_join(handler.settings['base_url'], 'lab')}"
                ),
            )

        handler.redirect(
            f"{self._proxy_url(sandbox)}/auth/{action}?"
            + urlencode({"return_to": return_to})
        )

    def _create_requests_for_server(
        self,
        sandbox: bool,
        proxy_session,
    ) -> ZenodoRequests:
        if proxy_session is None:
            return ZenodoRequests(url=self._server_url(sandbox))

        return ZenodoRequests(
            url=self._proxy_url(sandbox),
            headers=_cookie_header(
                self._proxy_session_cookie_name(sandbox),
                proxy_session.value,
            ),
        )

    def _server_url(self, sandbox: bool) -> str:
        return self.sandbox_url if sandbox else self.production_url

    def _proxy_url(self, sandbox: bool) -> str:
        return (
            self.sandbox_proxy_public_url
            if sandbox
            else self.production_proxy_public_url
        )

    def _proxy_session_cookie_name(self, sandbox: bool) -> str:
        return (
            self.sandbox_proxy_session_cookie_name
            if sandbox
            else self.production_proxy_session_cookie_name
        )
