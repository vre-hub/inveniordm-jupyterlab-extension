from __future__ import annotations

import json
from collections.abc import Callable
from http import HTTPStatus
from typing import Any
from urllib.error import HTTPError, URLError

import tornado.web

from .auth_service import (
    OAuthCallback,
    OAuthClientConfig,
    OAuthConfigurationError,
    OAuthStateError,
    OAuthTokenResponseError,
    create_oauth_login,
    exchange_oauth_code,
)

IsAllowedReturnTo = Callable[[str], bool]
OnOAuthSuccess = Callable[[tornado.web.RequestHandler, OAuthCallback], None]
SaveOAuthState = Callable[[str, str], None]
PopOAuthState = Callable[[str], str | None]


def write_json(
    handler: tornado.web.RequestHandler,
    payload: dict[str, Any],
    status: HTTPStatus = HTTPStatus.OK,
) -> None:
    handler.set_status(status)
    handler.set_header("Content-Type", "application/json")
    handler.finish(json.dumps(payload, indent=2))


def begin_inveniordm_oauth_login(
    handler: tornado.web.RequestHandler,
    *,
    oauth_config: OAuthClientConfig,
    save_oauth_state: SaveOAuthState,
    default_return_to: str,
    is_allowed_return_to: IsAllowedReturnTo,
    state_cookie_name: str | None = None,
) -> None:
    return_to = handler.get_query_argument("return_to", default_return_to)
    if not is_allowed_return_to(return_to):
        write_json(
            handler,
            {"message": "Invalid return_to URL"},
            HTTPStatus.BAD_REQUEST,
        )
        return

    try:
        login = create_oauth_login(oauth_config)
    except OAuthConfigurationError as error:
        write_json(
            handler,
            {"message": str(error)},
            HTTPStatus.SERVICE_UNAVAILABLE,
        )
        return

    save_oauth_state(login.state, return_to)
    if state_cookie_name is not None:
        handler.set_cookie(
            state_cookie_name,
            login.state,
            path="/",
            max_age=600,
            httponly=True,
            samesite="Lax",
        )
    handler.redirect(login.authorize_url)


def finish_inveniordm_oauth_callback(
    handler: tornado.web.RequestHandler,
    *,
    oauth_config: OAuthClientConfig,
    pop_oauth_state: PopOAuthState,
    on_success: OnOAuthSuccess,
    state_cookie_name: str | None = None,
) -> None:
    error = handler.get_query_argument("error", None)
    if error:
        write_json(
            handler,
            {"message": f"InvenioRDM OAuth returned an error: {error}"},
            HTTPStatus.BAD_REQUEST,
        )
        return

    code = handler.get_query_argument("code", None)
    state = handler.get_query_argument("state", None)
    if not code or not state:
        write_json(
            handler,
            {"message": "Missing code or state"},
            HTTPStatus.BAD_REQUEST,
        )
        return

    if state_cookie_name is not None and handler.get_cookie(state_cookie_name) != state:
        write_json(
            handler,
            {"message": "OAuth state cookie mismatch"},
            HTTPStatus.BAD_REQUEST,
        )
        return

    try:
        return_to = pop_oauth_state(state)
        if return_to is None:
            raise OAuthStateError("Unknown or expired OAuth state")
        token = exchange_oauth_code(oauth_config, code=code)
        callback = OAuthCallback(
            return_to=return_to,
            inveniordm_user_id=token.inveniordm_user_id,
            access_token=token.access_token,
            token_response=token.token_response,
        )
    except OAuthStateError as error:
        write_json(handler, {"message": str(error)}, HTTPStatus.BAD_REQUEST)
        return
    except OAuthTokenResponseError as error:
        write_json(handler, {"message": str(error)}, HTTPStatus.BAD_GATEWAY)
        return
    except HTTPError as error:
        # A 4xx here means the grant or the client registration is wrong (an
        # expired authorization code, a bad client secret, a redirect_uri
        # mismatch), not that the upstream is unhealthy. Reporting those as
        # 502 sends whoever is debugging to the wrong layer.
        status = (
            HTTPStatus.BAD_REQUEST
            if 400 <= error.code < 500
            else HTTPStatus.BAD_GATEWAY
        )
        write_json(
            handler,
            {
                "message": "InvenioRDM OAuth request failed",
                "status": error.code,
                "body": error.read().decode("utf-8", errors="replace"),
            },
            status,
        )
        return
    except URLError as error:
        write_json(
            handler,
            {"message": f"Could not reach InvenioRDM: {error.reason}"},
            HTTPStatus.BAD_GATEWAY,
        )
        return

    if state_cookie_name is not None:
        handler.clear_cookie(state_cookie_name, path="/")
    on_success(handler, callback)
