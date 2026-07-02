from __future__ import annotations

from urllib.parse import urlparse

from .config import Config


def is_allowed_return_to(return_to: str, config: Config) -> bool:
    parsed = urlparse(return_to)
    if parsed.scheme not in {"http", "https"}:
        return False
    return parsed.hostname in config.allowed_return_hosts


def is_hop_by_hop_header(name: str) -> bool:
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
