from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_INVENIORDM_BASE_URL = "https://sandbox.zenodo.org"
DEFAULT_PROXY_HOST = "127.0.0.1"
DEFAULT_PROXY_PORT = 8001
DEFAULT_PROXY_PUBLIC_URL = "http://127.0.0.1:8001"
DEFAULT_SCOPE = "user:email"
DEFAULT_ALLOWED_RETURN_HOSTS = ("localhost", "127.0.0.1", "::1")
DEFAULT_ALLOWED_CORS_ORIGINS = ("http://localhost:8888", "http://127.0.0.1:8888")
DEFAULT_SESSION_COOKIE_NAME = "zenodo_sandbox_proxy_session"
DEFAULT_CLIENT_ID = "ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU"


@dataclass(frozen=True)
class Config:
    client_id: str
    inveniordm_base_url: str = DEFAULT_INVENIORDM_BASE_URL
    session_cookie_name: str = DEFAULT_SESSION_COOKIE_NAME
    client_secret: str = ""
    proxy_host: str = DEFAULT_PROXY_HOST
    proxy_port: int = DEFAULT_PROXY_PORT
    proxy_public_url: str = DEFAULT_PROXY_PUBLIC_URL
    scope: str = DEFAULT_SCOPE
    allowed_return_hosts: tuple[str, ...] = DEFAULT_ALLOWED_RETURN_HOSTS
    allowed_cors_origins: tuple[str, ...] = DEFAULT_ALLOWED_CORS_ORIGINS

    @property
    def redirect_uri(self) -> str:
        return f"{self.proxy_public_url.rstrip('/')}/auth/callback"

    @property
    def oauth_state_cookie_name(self) -> str:
        return f"{self.session_cookie_name}_oauth_state"

    @classmethod
    def from_environment(cls) -> "Config":
        return cls(
            client_id=os.environ.get("INVENIORDM_CLIENT_ID", DEFAULT_CLIENT_ID),
            inveniordm_base_url=os.environ.get(
                "INVENIORDM_BASE_URL",
                DEFAULT_INVENIORDM_BASE_URL,
            ).rstrip("/"),
            client_secret=os.environ.get("INVENIORDM_CLIENT_SECRET", ""),
            proxy_host=os.environ.get("PROXY_HOST", DEFAULT_PROXY_HOST),
            proxy_port=int(os.environ.get("PROXY_PORT", str(DEFAULT_PROXY_PORT))),
            proxy_public_url=os.environ.get(
                "PROXY_PUBLIC_URL",
                DEFAULT_PROXY_PUBLIC_URL,
            ).rstrip("/"),
            scope=os.environ.get("INVENIORDM_OAUTH_SCOPE", DEFAULT_SCOPE),
            allowed_return_hosts=_split_env(
                "PROXY_ALLOWED_RETURN_HOSTS",
                DEFAULT_ALLOWED_RETURN_HOSTS,
            ),
            allowed_cors_origins=_split_env(
                "PROXY_ALLOWED_CORS_ORIGINS",
                DEFAULT_ALLOWED_CORS_ORIGINS,
            ),
            session_cookie_name=os.environ.get(
                "INVENIORDM_PROXY_SESSION_COOKIE_NAME",
                DEFAULT_SESSION_COOKIE_NAME,
            ),
        )


def _split_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.environ.get(name)
    if not value:
        return default
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Set {name} before starting the proxy")
    return value
