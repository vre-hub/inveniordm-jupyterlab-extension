from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class OAuthLogin:
    state: str
    authorize_url: str


@dataclass(frozen=True)
class OAuthClientConfig:
    inveniordm_base_url: str
    client_id: str
    redirect_uri: str
    scope: str
    client_secret: str | None = None


@dataclass(frozen=True)
class OAuthToken:
    inveniordm_user_id: str
    access_token: str
    token_response: dict[str, Any]


@dataclass(frozen=True)
class OAuthCallback:
    return_to: str
    inveniordm_user_id: str
    access_token: str
    token_response: dict[str, Any]


class OAuthConfigurationError(ValueError):
    pass


class OAuthStateError(ValueError):
    pass


class OAuthTokenResponseError(ValueError):
    pass


def create_oauth_state() -> str:
    return secrets.token_urlsafe(32)


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


def create_oauth_login(
    config: OAuthClientConfig,
    *,
    state: str | None = None,
) -> OAuthLogin:
    if not config.client_id:
        raise OAuthConfigurationError(
            "OAuth login is not configured for this remote server."
        )

    state = state or create_oauth_state()
    authorize_url = (
        f"{config.inveniordm_base_url.rstrip('/')}/oauth/authorize?"
        + urlencode(
            {
                "response_type": "code",
                "client_id": config.client_id,
                "redirect_uri": config.redirect_uri,
                "scope": config.scope,
                "state": state,
            }
        )
    )
    return OAuthLogin(state=state, authorize_url=authorize_url)


def exchange_oauth_code(
    config: OAuthClientConfig,
    *,
    code: str,
) -> OAuthToken:
    form_data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
    }
    if config.client_secret:
        form_data["client_secret"] = config.client_secret

    token_response = _form_post_json(
        f"{config.inveniordm_base_url.rstrip('/')}/oauth/token",
        form_data=form_data,
    )

    try:
        access_token = token_response["access_token"]
        inveniordm_user_id = str(token_response["user"]["id"])
    except KeyError as error:
        raise OAuthTokenResponseError(
            "InvenioRDM token response did not include access_token or user.id"
        ) from error

    return OAuthToken(
        inveniordm_user_id=inveniordm_user_id,
        access_token=access_token,
        token_response=token_response,
    )
