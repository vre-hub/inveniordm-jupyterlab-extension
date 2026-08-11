import json
from collections.abc import Callable
from urllib.parse import urlencode

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join

from inveniordm_auth.remote_servers import RemoteServerId

from ..inveniordm_requests.inveniordm_requests_factory import get_remote_server_override


class ProxyInvenioRDMAuthController:
    def __init__(
        self,
        proxy_url: Callable[[RemoteServerId], str],
        default_remote_server_id: RemoteServerId,
    ):
        self._proxy_url = proxy_url
        self._default_remote_server_id = default_remote_server_id

    def login(self, handler: APIHandler) -> None:
        self._redirect_to_proxy_auth(handler, "login")

    def logout(self, handler: APIHandler) -> None:
        self._redirect_to_proxy_auth(handler, "logout")

    def callback(self, handler: APIHandler) -> None:
        # This should never be called, because the callback is handled by the proxy server.
        handler.set_status(400)
        handler.finish(
            json.dumps({"message": "Callback not handled by this controller"})
        )

    def _redirect_to_proxy_auth(self, handler: APIHandler, action: str) -> None:
        remote_server_id = (
            get_remote_server_override(handler) or self._default_remote_server_id
        )
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
            f"{self._proxy_url(remote_server_id)}/auth/{action}?"
            + urlencode({"return_to": return_to})
        )
