import json
import os
from abc import ABC, abstractmethod
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlencode

from jupyter_core.paths import jupyter_data_dir
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join

from .token_store import FileTokenStore, StoredToken, TokenStore
from .zenodo import is_zenodo_request_authenticated
from .zenodo_requests import AccessTokenStatus, ZenodoRequests


def default_token_store_path() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "tokens.json"


def get_user_token_id(handler: APIHandler) -> str:
    """
    Get a unique ID for the current user to associate with their access token.
    """
    return handler.current_user.username


def get_sandbox_override(handler: APIHandler) -> bool | None:
    if handler.get_query_argument("sandbox", None) is None:
        return None

    return handler.get_query_argument("sandbox", "false").lower() in ("1", "true")


def _cookie_header(cookie_name: str, cookie_value: str) -> dict[str, str]:
    cookie = SimpleCookie()
    cookie[cookie_name] = cookie_value
    return {"Cookie": cookie.output(header="", sep=";").strip()}


def _nonempty_cookie(cookie):
    if cookie is None or not cookie.value:
        return None

    return cookie

# TODO split this file

class ZenodoRequestsFactory(ABC):
    @abstractmethod
    def create_zenodo_requests(self, handler: APIHandler) -> ZenodoRequests:
        pass

    @abstractmethod
    def is_sandbox(self, zenodo_requests: ZenodoRequests) -> bool:
        """
        Check if the given ZenodoRequests instance is for the sandbox server.
        """
        pass


    # TODO move the following 4 methods somewhere else

    def get_access_token_status(self, handler: APIHandler) -> AccessTokenStatus:
        zenodo_requests = self.create_zenodo_requests(handler)
        authentication_present = bool(zenodo_requests.headers)
        return AccessTokenStatus(
            access_token_present=authentication_present,
            access_token_valid=(
                is_zenodo_request_authenticated(
                    base_url=zenodo_requests.url,
                    headers=zenodo_requests.headers,
                )
                if authentication_present
                else False
            ),
            sandbox=self.is_sandbox(zenodo_requests),
        )

    def handle_auth(self, handler: APIHandler, action: str) -> None:
        raise NotImplementedError("OAuth proxy authentication is not configured")

    def put_access_token(self, handler: APIHandler) -> None:
        raise NotImplementedError("Manual Zenodo access tokens are not configured")

    def delete_access_token(self, handler: APIHandler) -> None:
        raise NotImplementedError("Manual Zenodo access tokens are not configured")


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
            print(f"Creating ZenodoRequests for sandbox_override={sandbox_override}, cookie={cookie}")
            return self._create_requests_for_server(sandbox_override, cookie)

        if sandbox_cookie is not None and production_cookie is None:
            print(f"Creating ZenodoRequests for sandbox=True, cookie={sandbox_cookie}")
            return self._create_requests_for_server(True, sandbox_cookie)

        if production_cookie is not None:
            print(f"Creating ZenodoRequests for sandbox=False, cookie={production_cookie}")
            return self._create_requests_for_server(False, production_cookie)

        print(f"Creating ZenodoRequests for production_url={self.production_url} with no cookies")
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


class LocalZenodoRequestsFactory(ZenodoRequestsFactory):
    production_url = "https://zenodo.org"
    sandbox_url = "https://sandbox.zenodo.org"

    def __init__(self, token_store: TokenStore):
        self.token_store = token_store

    def create_zenodo_requests(self, handler: APIHandler) -> ZenodoRequests:
        sandbox_override = get_sandbox_override(handler)
        token = self.token_store.get_token(get_user_token_id(handler))

        if sandbox_override is not None:
            headers = self._headers_for_token(token, sandbox_override)
            return ZenodoRequests(
                url=self._server_url(sandbox_override),
                headers=headers,
            )

        if token is not None:
            return ZenodoRequests(
                url=self._server_url(token.sandbox),
                headers=self._headers_for_token(token, token.sandbox),
            )

        return ZenodoRequests(url=self.production_url)

    def is_sandbox(self, zenodo_requests: ZenodoRequests) -> bool:
        return zenodo_requests.url == self.sandbox_url

    def put_access_token(self, handler: APIHandler) -> None:
        data = handler.get_json_body() or {}
        access_token = data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            handler.set_status(400)
            handler.finish(json.dumps({"message": "Missing access_token"}))
            return

        headers = {"Authorization": f"Bearer {access_token}"}
        sandbox = self._check_if_token_is_sandbox(headers=headers)
        self.token_store.set_access_token(
            get_user_token_id(handler),
            access_token,
            True,
            sandbox=sandbox,
        )
        handler.finish(
            json.dumps(
                AccessTokenStatus(
                    access_token_present=True,
                    access_token_valid=True,
                    sandbox=sandbox,
                ).__dict__
            )
        )

    def delete_access_token(self, handler: APIHandler) -> None:
        self.token_store.remove_access_token(get_user_token_id(handler))
        handler.finish(json.dumps({"message": "Zenodo access token removed"}))

    def _headers_for_token(
        self,
        token: StoredToken | None,
        sandbox: bool,
    ) -> dict[str, str]:
        if token is None or token.sandbox != sandbox:
            return {}

        return {"Authorization": f"Bearer {token.access_token}"}

    def _server_url(self, sandbox: bool) -> str:
        return self.sandbox_url if sandbox else self.production_url

    def _check_if_token_is_sandbox(
        self,
        *,
        headers: dict[str, str],
    ) -> bool:
        sandbox = is_zenodo_request_authenticated(
            base_url=self.sandbox_url,
            headers=headers,
        )
        if sandbox:
            return True
        prod = is_zenodo_request_authenticated(
            base_url=self.production_url,
            headers=headers,
        )
        if prod:
            return False
        raise ValueError(
            "Access token is not valid"
        )


def create_zenodo_requests_factory(factory_type: str = "proxy") -> ZenodoRequestsFactory:
    if factory_type == "local":
        return LocalZenodoRequestsFactory(
            FileTokenStore(
                os.environ.get(
                    "ZENODO_JUPYTERLAB_TOKEN_STORE",
                    str(default_token_store_path()),
                )
            )
        )
    if factory_type == "proxy":
        return ProxyZenodoRequestsFactory()

    raise ValueError(
        "ZENODO_JUPYTERLAB_REQUESTS_FACTORY must be either 'proxy' or 'local'"
    )
