from __future__ import annotations

import json
from collections.abc import Callable
from http import HTTPStatus
from typing import Any
from urllib.error import HTTPError, URLError

import tornado.web

from .auth_service import (
    OAuthCallback,
    OAuthConfigurationError,
    OAuthStateError,
    OAuthTokenResponseError,
    ZenodoAuthService,
)

IsAllowedReturnTo = Callable[[str], bool]
OnOAuthSuccess = Callable[[tornado.web.RequestHandler, OAuthCallback], None]


def write_json(
    handler: tornado.web.RequestHandler,
    payload: dict[str, Any],
    status: HTTPStatus = HTTPStatus.OK,
) -> None:
    handler.set_status(status)
    handler.set_header("Content-Type", "application/json")
    handler.finish(json.dumps(payload, indent=2))


def begin_zenodo_oauth_login(
    handler: tornado.web.RequestHandler,
    *,
    auth_service: ZenodoAuthService,
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
        login = auth_service.begin_login(return_to)
    except OAuthConfigurationError as error:
        write_json(
            handler,
            {"message": str(error)},
            HTTPStatus.SERVICE_UNAVAILABLE,
        )
        return

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


def finish_zenodo_oauth_callback(
    handler: tornado.web.RequestHandler,
    *,
    auth_service: ZenodoAuthService,
    on_success: OnOAuthSuccess,
    state_cookie_name: str | None = None,
) -> None:
    error = handler.get_query_argument("error", None)
    if error:
        write_json(
            handler,
            {"message": f"Zenodo OAuth returned an error: {error}"},
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

    if (
        state_cookie_name is not None
        and handler.get_cookie(state_cookie_name) != state
    ):
        write_json(
            handler,
            {"message": "OAuth state cookie mismatch"},
            HTTPStatus.BAD_REQUEST,
        )
        return

    try:
        callback = auth_service.finish_login(code=code, state=state)
    except OAuthStateError as error:
        write_json(handler, {"message": str(error)}, HTTPStatus.BAD_REQUEST)
        return
    except OAuthTokenResponseError as error:
        write_json(handler, {"message": str(error)}, HTTPStatus.BAD_GATEWAY)
        return
    except HTTPError as error:
        write_json(
            handler,
            {
                "message": "Zenodo OAuth request failed",
                "status": error.code,
                "body": error.read().decode("utf-8", errors="replace"),
            },
            HTTPStatus.BAD_GATEWAY,
        )
        return
    except URLError as error:
        write_json(
            handler,
            {"message": f"Could not reach Zenodo: {error.reason}"},
            HTTPStatus.BAD_GATEWAY,
        )
        return

    if state_cookie_name is not None:
        handler.clear_cookie(state_cookie_name, path="/")
    on_success(handler, callback)
