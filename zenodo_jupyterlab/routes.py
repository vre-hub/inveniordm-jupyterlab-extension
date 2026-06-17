import json
from pathlib import Path

from jupyter_server.base.handlers import APIHandler
from jupyter_core.paths import jupyter_data_dir
from jupyter_server.utils import url_path_join
import tornado

from .token_store import FileTokenStore, TokenStore


def _default_token_store_path() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "tokens.json"


def _get_user_token_id(handler: APIHandler) -> str:
    """
    Get a unique ID for the current user to associate with their access token.
    This uses the "username" field, which is only stable and secure if user accounts are not
    renamed or remapped.
    TODO we might want to allow to specify to use a different field than username
    depending on auth provider,
    if some auth providers have better options available
    """
    return handler.current_user.username


class HelloRouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": (
                "Hello, world!"
                " This is the '/zenodo-jupyterlab/hello' endpoint."
                " Try visiting me in your browser!"
            ),
        }))

class ZenodoAccessTokenHandler(APIHandler):
    def initialize(self, token_store: TokenStore):
        self.token_store = token_store

    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        token_id = _get_user_token_id(self)
        self.finish(json.dumps({
            "access_token_present": self.token_store.has_access_token(token_id)
        }))

    @tornado.web.authenticated
    def put(self):
        data = self.get_json_body() or {}
        access_token = data.get("access_token")
        if not access_token:
            self.set_status(400)
            self.finish(json.dumps({"error": "Missing 'access_token' in request body"}))
            return

        token_id = _get_user_token_id(self)
        self.token_store.set_access_token(token_id, access_token)

        self.finish(json.dumps({"message": "Access token received successfully"}))

    @tornado.web.authenticated
    def delete(self):
        token_id = _get_user_token_id(self)
        self.token_store.remove_access_token(token_id)
        self.finish(json.dumps({"message": "Access token removed successfully"}))


def setup_route_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    token_store = FileTokenStore(_default_token_store_path())

    zenodo_base_url = url_path_join(base_url, "zenodo-jupyterlab")
    handlers = [
        (url_path_join(zenodo_base_url, "hello"), HelloRouteHandler),
        (
            url_path_join(zenodo_base_url, "access-token"),
            ZenodoAccessTokenHandler,
            {"token_store": token_store},
        ),
    ]

    web_app.add_handlers(host_pattern, handlers)
