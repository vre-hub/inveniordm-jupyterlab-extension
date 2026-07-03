from collections.abc import Callable
import json
from urllib.parse import urlencode

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join

from ..zenodo_requests.zenodo_requests_factory import get_sandbox_override


class ProxyZenodoAuthController:
    def __init__(self, proxy_url: Callable[[bool], str]):
        self._proxy_url = proxy_url

    def login(self, handler: APIHandler) -> None:
        self._redirect_to_proxy_auth(handler, "login")

    def logout(self, handler: APIHandler) -> None:
        self._redirect_to_proxy_auth(handler, "logout")

    def callback(self, handler: APIHandler) -> None:
        # This should never be called, because the callback is handled by the proxy server.
        handler.set_status(400)
        handler.finish(json.dumps({"message": "Callback not handled by this controller"}))

    def _redirect_to_proxy_auth(self, handler: APIHandler, action: str) -> None:
        sandbox_override = get_sandbox_override(handler)
        sandbox = sandbox_override if sandbox_override is not None else False
        return_to = handler.get_query_argument("return_to", None)
        if return_to is None:
            return_to = handler.request.headers.get(
                "Referer",
                (
                    f"{handler.request.protocol}://{handler.request.host}"
                    f"{url_path_join(handler.settings['base_url'], 'lab')}"
                ),
            )

        handler.redirect(
            f"{self._proxy_url(sandbox)}/auth/{action}?"
            + urlencode({"return_to": return_to})
        )
