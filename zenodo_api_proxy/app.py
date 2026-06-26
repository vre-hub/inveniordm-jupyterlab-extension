"""
Auth-only MVP for the Zenodo API proxy.

This deliberately keeps state in memory and only proves the OAuth login flow
against the Zenodo sandbox. It is not production storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import secrets
from http import HTTPStatus
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import tornado.httpserver
import tornado.ioloop
import tornado.web

from .config import Config

SESSION_COOKIE_NAME = "zenodo_proxy_session"
OAUTH_STATE_COOKIE_NAME = "zenodo_proxy_oauth_state"

@dataclass
class ProxyState:
    oauth_states: dict[str, str] = field(default_factory=dict)
    sessions: dict[str, dict[str, Any]] = field(default_factory=dict)


def _json_request(url: str, *, access_token: str, timeout: int = 10) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _form_post_json(
    url: str,
    *,
    form_data: dict[str, str],
    timeout: int = 10,
) -> dict[str, Any]:
    body = urlencode(form_data).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _is_allowed_return_to(return_to: str, config: Config) -> bool:
    parsed = urlparse(return_to)
    if parsed.scheme not in {"http", "https"}:
        return False
    return parsed.hostname in config.allowed_return_hosts


def _is_hop_by_hop_header(name: str) -> bool:
    return name.lower() in {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }


class BaseProxyHandler(tornado.web.RequestHandler):
    @property
    def config(self) -> Config:
        return self.settings["proxy_config"]

    @property
    def state(self) -> ProxyState:
        return self.settings["proxy_state"]

    def set_default_headers(self) -> None:
        origin = self.request.headers.get("Origin")
        if origin in self.config.allowed_cors_origins:
            self.set_header("Access-Control-Allow-Origin", origin)
            self.set_header("Access-Control-Allow-Credentials", "true")
            self.set_header("Vary", "Origin")
        self.set_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        )
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Cache-Control", "no-store")

    def options(self, *args: str, **kwargs: str) -> None:
        self.set_status(HTTPStatus.NO_CONTENT)
        self.finish()

    def write_json(
        self,
        payload: dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(payload, indent=2))

    def set_proxy_cookie(
        self,
        name: str,
        value: str,
        *,
        max_age: int,
        same_site: str,
    ) -> None:
        self.set_cookie(
            name,
            value,
            path="/",
            max_age=max_age,
            httponly=True,
            samesite=same_site,
        )

    def expire_proxy_cookie(self, name: str) -> None:
        self.set_proxy_cookie(name, "", max_age=0, same_site="Lax")

    def current_session(self) -> dict[str, Any] | None:
        session_id = self.get_cookie(SESSION_COOKIE_NAME)
        if not session_id:
            return None
        return self.state.sessions.get(session_id)


class HealthHandler(BaseProxyHandler):
    def get(self) -> None:
        self.write_json({"ok": True, "zenodo_base_url": self.config.zenodo_base_url})


class LoginHandler(BaseProxyHandler):
    def get(self) -> None:
        if not self.config.client_id or not self.config.client_secret:
            self.write_json(
                {
                    "message": (
                        "Set ZENODO_CLIENT_ID and ZENODO_CLIENT_SECRET before "
                        "starting OAuth login."
                    )
                },
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        return_to = self.get_query_argument("return_to", self.config.proxy_public_url)
        if not _is_allowed_return_to(return_to, self.config):
            self.write_json({"message": "Invalid return_to URL"}, HTTPStatus.BAD_REQUEST)
            return

        state = secrets.token_urlsafe(32)
        self.state.oauth_states[state] = return_to
        authorize_url = (
            f"{self.config.zenodo_base_url}/oauth/authorize?"
            + urlencode(
                {
                    "response_type": "code",
                    "client_id": self.config.client_id,
                    "redirect_uri": self.config.redirect_uri,
                    "scope": self.config.scope,
                    "state": state,
                }
            )
        )
        self.set_proxy_cookie(
            OAUTH_STATE_COOKIE_NAME,
            state,
            max_age=600,
            same_site="Lax",
        )
        self.redirect(authorize_url)


class CallbackHandler(BaseProxyHandler):
    def get(self) -> None:
        error = self.get_query_argument("error", None)
        if error:
            self.write_json(
                {"message": f"Zenodo OAuth returned an error: {error}"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        code = self.get_query_argument("code", None)
        state = self.get_query_argument("state", None)
        if not code or not state:
            self.write_json({"message": "Missing code or state"}, HTTPStatus.BAD_REQUEST)
            return

        if self.get_cookie(OAUTH_STATE_COOKIE_NAME) != state:
            self.write_json(
                {"message": "OAuth state cookie mismatch"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        return_to = self.state.oauth_states.pop(state, None)
        if return_to is None:
            self.write_json(
                {"message": "Unknown or expired OAuth state"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            token_response = _form_post_json(
                f"{self.config.zenodo_base_url}/oauth/token",
                form_data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "redirect_uri": self.config.redirect_uri,
                },
            )
            """
            print("Zenodo token response keys:", sorted(token_response.keys()))
            print("Zenodo token response expires_in:", token_response.get("expires_in"))
            print("Zenodo token response scope:", token_response.get("scope"))
            print("Zenodo token response user:", token_response.get("user")) # {'id': '12345'}
            """
            access_token = token_response["access_token"]
            me = _json_request(
                f"{self.config.zenodo_base_url}/api/me",
                access_token=access_token,
            )
        except KeyError:
            self.write_json(
                {"message": "Zenodo token response did not include access_token"},
                HTTPStatus.BAD_GATEWAY,
            )
            return
        except HTTPError as error:
            self.write_json(
                {
                    "message": "Zenodo OAuth request failed",
                    "status": error.code,
                    "body": error.read().decode("utf-8", errors="replace"),
                },
                HTTPStatus.BAD_GATEWAY,
            )
            return
        except URLError as error:
            self.write_json(
                {"message": f"Could not reach Zenodo: {error.reason}"},
                HTTPStatus.BAD_GATEWAY,
            )
            return

        session_id = secrets.token_urlsafe(32)
        self.state.sessions[session_id] = {
            "zenodo_user_id": str(me["id"]),
            "access_token": access_token,
            "me": me,
        }
        self.set_proxy_cookie(
            SESSION_COOKIE_NAME,
            session_id,
            max_age=60 * 60 * 24 * 14,
            same_site="Lax",
        )
        self.expire_proxy_cookie(OAUTH_STATE_COOKIE_NAME)
        self.redirect(return_to)


class StatusHandler(BaseProxyHandler):
    def get(self) -> None:
        session = self.current_session()
        if session is None:
            self.write_json({"authenticated": False})
            return

        self.write_json(
            {
                "authenticated": True,
                "zenodo_base_url": self.config.zenodo_base_url,
                "zenodo_user_id": session["zenodo_user_id"],
                "me": _public_me(session["me"]),
            }
        )


class LogoutHandler(BaseProxyHandler):
    def get(self) -> None:
        session_id = self.get_cookie(SESSION_COOKIE_NAME)
        if session_id:
            self.state.sessions.pop(session_id, None)
        self.expire_proxy_cookie(SESSION_COOKIE_NAME)
        self.write_json({"authenticated": False})

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
        session = self.current_session()
        if session is None:
            self.write_json(
                {"message": "Missing or expired proxy session"},
                HTTPStatus.UNAUTHORIZED,
            )
            return

        target_url = f"{self.config.zenodo_base_url}/api{path or ''}"
        if self.request.query:
            target_url = f"{target_url}?{self.request.query}"

        request = Request(
            target_url,
            data=self.request.body or None,
            headers=self.forward_request_headers(session["access_token"]),
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
            if _is_hop_by_hop_header(name):
                continue
            lower_name = name.lower()
            if lower_name in {"content-length", "server", "date", "set-cookie"}:
                continue
            if lower_name.startswith("access-control-"):
                continue
            self.set_header(name, value)
        self.finish(body)


class JsonNotFoundHandler(BaseProxyHandler):
    def prepare(self) -> None:
        self.write_json({"message": "Not found"}, HTTPStatus.NOT_FOUND)


def _public_me(me: dict[str, Any]) -> dict[str, Any]:
    return {
        key: me[key]
        for key in ("id", "email", "username", "full_name", "displayname")
        if key in me
    }


def create_app(
    config: Config,
    state: ProxyState | None = None,
) -> tornado.web.Application:
    proxy_state = state or ProxyState()
    return tornado.web.Application(
        [
            (r"/health", HealthHandler),
            (r"/auth/login", LoginHandler),
            (r"/auth/callback", CallbackHandler),
            (r"/auth/status", StatusHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/api(/.*)?", ApiProxyHandler),
            (r"/.*", JsonNotFoundHandler),
        ],
        proxy_config=config,
        proxy_state=proxy_state,
    )


def create_server(
    config: Config,
    host: str,
    port: int,
    state: ProxyState | None = None,
) -> tornado.httpserver.HTTPServer:
    app = create_app(config, state)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port, address=host)
    return server


def main() -> None:
    config = Config.from_environment()
    create_server(config, config.proxy_host, config.proxy_port)
    print(
        "Zenodo API proxy MVP listening on "
        f"http://{config.proxy_host}:{config.proxy_port}"
    )
    print(f"Zenodo base URL: {config.zenodo_base_url}")
    print(f"OAuth redirect URI: {config.redirect_uri}")
    tornado.ioloop.IOLoop.current().start()
