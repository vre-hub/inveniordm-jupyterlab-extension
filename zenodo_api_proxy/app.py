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
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

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


class ProxyHandler(BaseHTTPRequestHandler):
    server_version = "ZenodoApiProxyMVP/0.1"

    @property
    def config(self) -> Config:
        return self.server.config  # type: ignore[attr-defined]

    @property
    def state(self) -> ProxyState:
        return self.server.state  # type: ignore[attr-defined]

    def do_OPTIONS(self) -> None:
        self._send_empty(HTTPStatus.NO_CONTENT)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json({"ok": True, "zenodo_base_url": self.config.zenodo_base_url})
            return
        if path == "/auth/login":
            self._handle_login()
            return
        if path == "/auth/callback":
            self._handle_callback()
            return
        if path == "/auth/status":
            self._handle_status()
            return
        if path == "/auth/logout":
            self._handle_logout()
            return
        self._send_json({"message": "Not found"}, HTTPStatus.NOT_FOUND)

    def _handle_login(self) -> None:
        if not self.config.client_id or not self.config.client_secret:
            self._send_json(
                {
                    "message": (
                        "Set ZENODO_CLIENT_ID and ZENODO_CLIENT_SECRET before "
                        "starting OAuth login."
                    )
                },
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return

        query = parse_qs(urlparse(self.path).query)
        return_to = query.get("return_to", [self.config.proxy_public_url])[0]
        if not _is_allowed_return_to(return_to, self.config):
            self._send_json({"message": "Invalid return_to URL"}, HTTPStatus.BAD_REQUEST)
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
        self._redirect(
            authorize_url,
            cookies=[
                self._cookie(
                    OAUTH_STATE_COOKIE_NAME,
                    state,
                    max_age=600,
                    same_site="Lax",
                )
            ],
        )

    def _handle_callback(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        error = query.get("error", [None])[0]
        if error:
            self._send_json(
                {"message": f"Zenodo OAuth returned an error: {error}"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        code = query.get("code", [None])[0]
        state = query.get("state", [None])[0]
        if not code or not state:
            self._send_json({"message": "Missing code or state"}, HTTPStatus.BAD_REQUEST)
            return

        if self._cookies().get(OAUTH_STATE_COOKIE_NAME) != state:
            self._send_json({"message": "OAuth state cookie mismatch"}, HTTPStatus.BAD_REQUEST)
            return

        return_to = self.state.oauth_states.pop(state, None)
        if return_to is None:
            self._send_json({"message": "Unknown or expired OAuth state"}, HTTPStatus.BAD_REQUEST)
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
            access_token = token_response["access_token"]
            me = _json_request(
                f"{self.config.zenodo_base_url}/api/me",
                access_token=access_token,
            )
        except KeyError:
            self._send_json(
                {"message": "Zenodo token response did not include access_token"},
                HTTPStatus.BAD_GATEWAY,
            )
            return
        except HTTPError as error:
            self._send_json(
                {
                    "message": "Zenodo OAuth request failed",
                    "status": error.code,
                    "body": error.read().decode("utf-8", errors="replace"),
                },
                HTTPStatus.BAD_GATEWAY,
            )
            return
        except URLError as error:
            self._send_json(
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
        self._redirect(
            return_to,
            cookies=[
                self._cookie(
                    SESSION_COOKIE_NAME,
                    session_id,
                    max_age=60 * 60 * 24 * 14,
                    same_site="Lax",
                ),
                self._expired_cookie(OAUTH_STATE_COOKIE_NAME),
            ],
        )

    def _handle_status(self) -> None:
        session = self._current_session()
        if session is None:
            self._send_json({"authenticated": False})
            return

        self._send_json(
            {
                "authenticated": True,
                "zenodo_base_url": self.config.zenodo_base_url,
                "zenodo_user_id": session["zenodo_user_id"],
                "me": _public_me(session["me"]),
            }
        )

    def _handle_logout(self) -> None:
        session_id = self._cookies().get(SESSION_COOKIE_NAME)
        if session_id:
            self.state.sessions.pop(session_id, None)
        self._send_json(
            {"authenticated": False},
            cookies=[self._expired_cookie(SESSION_COOKIE_NAME)],
        )

    def _current_session(self) -> dict[str, Any] | None:
        session_id = self._cookies().get(SESSION_COOKIE_NAME)
        if not session_id:
            return None
        return self.state.sessions.get(session_id)

    def _cookies(self) -> dict[str, str]:
        header = self.headers.get("Cookie")
        if not header:
            return {}
        cookie = SimpleCookie()
        cookie.load(header)
        return {key: morsel.value for key, morsel in cookie.items()}

    def _send_json(
        self,
        payload: dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK,
        *,
        cookies: list[str] | None = None,
    ) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for cookie in cookies or []:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(
        self,
        status: HTTPStatus,
        *,
        cookies: list[str] | None = None,
    ) -> None:
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Length", "0")
        for cookie in cookies or []:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _redirect(self, location: str, *, cookies: list[str] | None = None) -> None:
        self.send_response(HTTPStatus.FOUND)
        self._send_common_headers()
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        for cookie in cookies or []:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _send_common_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin in self.config.allowed_cors_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def _cookie(
        self,
        name: str,
        value: str,
        *,
        max_age: int,
        same_site: str,
    ) -> str:
        cookie = SimpleCookie()
        cookie[name] = value
        cookie[name]["path"] = "/"
        cookie[name]["max-age"] = str(max_age)
        cookie[name]["httponly"] = True
        cookie[name]["samesite"] = same_site
        return cookie.output(header="").strip()

    def _expired_cookie(self, name: str) -> str:
        cookie = SimpleCookie()
        cookie[name] = ""
        cookie[name]["path"] = "/"
        cookie[name]["max-age"] = "0"
        cookie[name]["httponly"] = True
        cookie[name]["samesite"] = "Lax"
        return cookie.output(header="").strip()


def _public_me(me: dict[str, Any]) -> dict[str, Any]:
    return {
        key: me[key]
        for key in ("id", "email", "username", "full_name", "displayname")
        if key in me
    }


class ZenodoProxyServer(ThreadingHTTPServer):
    config: Config
    state: ProxyState


def create_server(config: Config, host: str, port: int) -> ZenodoProxyServer:
    server = ZenodoProxyServer((host, port), ProxyHandler)
    server.config = config
    server.state = ProxyState()
    return server


def main() -> None:
    config = Config.from_environment()
    server = create_server(config, config.proxy_host, config.proxy_port)
    print(
        "Zenodo API proxy MVP listening on "
        f"http://{config.proxy_host}:{config.proxy_port}"
    )
    print(f"Zenodo base URL: {config.zenodo_base_url}")
    print(f"OAuth redirect URI: {config.redirect_uri}")
    server.serve_forever()
