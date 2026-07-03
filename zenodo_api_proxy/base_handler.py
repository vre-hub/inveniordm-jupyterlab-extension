from __future__ import annotations

import json
from http import HTTPStatus
from typing import Any

import tornado.web

from zenodo_auth import OAuthClientConfig
from zenodo_auth.token_store import MultiTokenStore

from .config import Config
from .types import ProxyState


class BaseProxyHandler(tornado.web.RequestHandler):
    @property
    def config(self) -> Config:
        return self.settings["proxy_config"]

    @property
    def state(self) -> ProxyState:
        return self.settings["proxy_state"]

    @property
    def oauth_config(self) -> OAuthClientConfig:
        return self.settings["zenodo_oauth_config"]

    @property
    def token_store(self) -> MultiTokenStore:
        return self.settings["zenodo_token_store"]

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

    def current_zenodo_user_id(self) -> str | None:
        session_id = self.get_cookie(self.config.session_cookie_name)
        if not session_id:
            return None
        return self.state.sessions.get(session_id)
