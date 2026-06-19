import json
import os
from pathlib import Path

from jupyter_server.base.handlers import APIHandler
from jupyter_core.paths import jupyter_data_dir
from jupyter_server.utils import url_path_join
import tornado
import requests

from .token_store import FileTokenStore, TokenStore
from .zenodo import (
    is_zenodo_access_token_valid,
    list_zenodo_depositions,
    search_zenodo_records,
)


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
        token = self.token_store.get_token(token_id)
        self.finish(json.dumps({
            "access_token_present": token is not None,
            "access_token_valid": (
                token.access_token_valid
                if token is not None
                else False
            ),
            "sandbox": token.sandbox if token is not None else False,
        }))

    @tornado.web.authenticated
    def put(self):
        data = self.get_json_body() or {}
        access_token = data.get("access_token")
        sandbox = data.get("sandbox")
        if not access_token:
            self.set_status(400)
            self.finish(json.dumps({"message": "Missing 'access_token' in request body"}))
            return
        if not isinstance(sandbox, bool):
            self.set_status(400)
            self.finish(json.dumps({"message": "Missing boolean 'sandbox' in request body"}))
            return

        access_token_valid = is_zenodo_access_token_valid(access_token, sandbox)
        if not access_token_valid:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid Zenodo access token"}))
            return

        token_id = _get_user_token_id(self)
        self.token_store.set_access_token(
            token_id, access_token, access_token_valid, sandbox
        )

        self.finish(json.dumps({"message": "Access token received successfully"}))

    @tornado.web.authenticated
    def delete(self):
        token_id = _get_user_token_id(self)
        self.token_store.remove_access_token(token_id)
        self.finish(json.dumps({"message": "Access token removed successfully"}))


class ZenodoRecordsHandler(APIHandler):
    def initialize(self, token_store: TokenStore):
        self.token_store = token_store

    @tornado.web.authenticated
    def get(self):
        token_id = _get_user_token_id(self)
        token = self.token_store.get_token(token_id)

        access_token = token.access_token if token is not None else None

        sandbox = False
        if self.get_query_argument("sandbox", None) is not None:
            sandbox = self.get_query_argument("sandbox", "false").lower() in ("1", "true")
        elif token is not None:
            sandbox = token.sandbox
        filters = {
            key: self.get_query_argument(key, None)
            for key in ("communities", "type", "subtype", "bounds", "custom")
        }
        filters = {key: value for key, value in filters.items() if value}

        try:
            # TODO refactor so we do not specify defaults twice (here and in zenodo.py)
            records = search_zenodo_records(
                self.get_query_argument("q", ""),
                access_token=access_token,
                sandbox=sandbox,
                page=int(self.get_query_argument("page", "1")),
                size=int(self.get_query_argument("size", "10")),
                sort=self.get_query_argument("sort", "bestmatch"),
                all_versions=self.get_query_argument("all_versions", "false").lower()
                in ("1", "true"),
                filters=filters,
            )
        except ValueError:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid page or size"}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(records))


class WhoAmIHandler(APIHandler):
    @tornado.web.authenticated
    def get(self):
        """
        Call this to make the extension backend make a dummy request to the JupyterHub service 
        to see if the current user is correctly authenticated at the service.
        """
        # call e.g. http://127.0.0.1:8000/user/elisabeth/zenodo-jupyterlab/whoami
        print("calling Zenodo JupyterHub service to check if user is authenticated")
        try:
            response = requests.get(
                "http://127.0.0.1:8000/services/zenodo-jupyterhub-service/whoami",
                headers={
                    "Authorization": f"token {os.environ['JUPYTERHUB_API_TOKEN']}"
                },
                timeout=5,
            )
            print(f"Zenodo JupyterHub service response: {response.status_code} {response.text}")
            response.raise_for_status()
        except KeyError:
            self.set_status(503)
            self.finish(json.dumps({"message": "JUPYTERHUB_API_TOKEN is not set"}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(response.text)


class ZenodoDepositionsHandler(APIHandler):
    def initialize(self, token_store: TokenStore):
        self.token_store = token_store

    @tornado.web.authenticated
    def get(self):
        token_id = _get_user_token_id(self)
        token = self.token_store.get_token(token_id)

        sandbox = token.sandbox if token is not None else False
        if self.get_query_argument("sandbox", None) is not None:
            sandbox = self.get_query_argument("sandbox", "false").lower() in ("1", "true")

        try:
            depositions = list_zenodo_depositions(
                access_token=token.access_token if token is not None else None,
                sandbox=sandbox,
                page=int(self.get_query_argument("page", "1")),
                size=int(self.get_query_argument("size", "10")),
            )
        except ValueError:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid page or size"}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(depositions))


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
        (
            url_path_join(zenodo_base_url, "records"),
            ZenodoRecordsHandler,
            {"token_store": token_store},
        ),
        (url_path_join(zenodo_base_url, "whoami"), WhoAmIHandler),
        (
            url_path_join(zenodo_base_url, "depositions"),
            ZenodoDepositionsHandler,
            {"token_store": token_store},
        ),
    ]

    web_app.add_handlers(host_pattern, handlers)
