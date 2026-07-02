from __future__ import annotations

from dataclasses import dataclass
import json
import secrets
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .token_store import MultiTokenStore, StoredToken


@dataclass(frozen=True)
class OAuthLogin:
    state: str
    authorize_url: str


@dataclass(frozen=True)
class OAuthCallback:
    return_to: str
    zenodo_user_id: str


class OAuthConfigurationError(ValueError):
    pass


class OAuthStateError(ValueError):
    pass


class OAuthTokenResponseError(ValueError):
    pass


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


class ZenodoAuthService:
    def __init__(
        self,
        *,
        zenodo_base_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: str,
        token_store: MultiTokenStore,
        sandbox: bool = False,
    ):
        self.zenodo_base_url = zenodo_base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.token_store = token_store
        self.sandbox = sandbox
        self.oauth_states: dict[str, str] = {}

    def begin_login(self, return_to: str) -> OAuthLogin:
        if not self.client_id or not self.client_secret:
            raise OAuthConfigurationError(
                "Set ZENODO_CLIENT_ID and ZENODO_CLIENT_SECRET before "
                "starting OAuth login."
            )

        state = secrets.token_urlsafe(32)
        self.oauth_states[state] = return_to
        authorize_url = (
            f"{self.zenodo_base_url}/oauth/authorize?"
            + urlencode(
                {
                    "response_type": "code",
                    "client_id": self.client_id,
                    "redirect_uri": self.redirect_uri,
                    "scope": self.scope,
                    "state": state,
                }
            )
        )
        return OAuthLogin(state=state, authorize_url=authorize_url)

    def finish_login(self, *, code: str, state: str) -> OAuthCallback:
        return_to = self.oauth_states.pop(state, None)
        if return_to is None:
            raise OAuthStateError("Unknown or expired OAuth state")

        token_response = _form_post_json(
            f"{self.zenodo_base_url}/oauth/token",
            form_data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
            },
        )

        try:
            access_token = token_response["access_token"]
            zenodo_user_id = str(token_response["user"]["id"])
        except KeyError as error:
            raise OAuthTokenResponseError(
                "Zenodo token response did not include access_token or user.id"
            ) from error

        self.token_store.set_token(
            zenodo_user_id,
            access_token,
            True,
            sandbox=self.sandbox,
        )
        return OAuthCallback(return_to=return_to, zenodo_user_id=zenodo_user_id)

    def get_token(self, zenodo_user_id: str) -> StoredToken | None:
        return self.token_store.get_token(zenodo_user_id)
