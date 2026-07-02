from __future__ import annotations

from http import HTTPStatus

from .base_handler import BaseProxyHandler
from .helpers import is_allowed_return_to


class LogoutHandler(BaseProxyHandler):
    def get(self) -> None:
        session_id = self.get_cookie(self.config.session_cookie_name)
        if session_id:
            self.state.sessions.pop(session_id, None)
        self.expire_proxy_cookie(self.config.session_cookie_name)
        return_to = self.get_query_argument("return_to", None)
        if return_to is not None:
            if not is_allowed_return_to(return_to, self.config):
                self.write_json(
                    {"message": "Invalid return_to URL"},
                    HTTPStatus.BAD_REQUEST,
                )
                return
            self.redirect(return_to)
            return
        self.write_json({"authenticated": False})
