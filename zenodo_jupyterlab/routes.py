import json
import os
from pathlib import Path

from jupyter_server.base.handlers import APIHandler
from jupyter_core.paths import jupyter_data_dir
from jupyter_server.utils import url_path_join
import tornado
import requests

from .token_store import FileTokenStore
from .zenodo_requests import ZenodoRequests


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
    def initialize(self, zenodo_requests: ZenodoRequests):
        self.zenodo_requests = zenodo_requests

    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        token_id = _get_user_token_id(self)
        status = self.zenodo_requests.get_access_token_status(token_id)
        self.finish(json.dumps(status.__dict__))

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

        token_id = _get_user_token_id(self)
        access_token_valid = self.zenodo_requests.set_access_token(
            token_id, access_token, sandbox
        )
        if not access_token_valid:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid Zenodo access token"}))
            return

        self.finish(json.dumps({"message": "Access token received successfully"}))

    @tornado.web.authenticated
    def delete(self):
        token_id = _get_user_token_id(self)
        self.zenodo_requests.remove_access_token(token_id)
        self.finish(json.dumps({"message": "Access token removed successfully"}))


class ZenodoRecordsHandler(APIHandler):
    def initialize(self, zenodo_requests: ZenodoRequests):
        self.zenodo_requests = zenodo_requests

    @tornado.web.authenticated
    def get(self):
        token_id = _get_user_token_id(self)

        sandbox_override = None
        if self.get_query_argument("sandbox", None) is not None:
            sandbox_override = self.get_query_argument("sandbox", "false").lower() in (
                "1",
                "true",
            )
        filters = {
            key: self.get_query_argument(key, None)
            for key in ("communities", "type", "subtype", "bounds", "custom")
        }
        filters = {key: value for key, value in filters.items() if value}

        try:
            # TODO refactor so we do not specify defaults twice (here and in zenodo.py)
            records = self.zenodo_requests.search_zenodo_records(
                token_id,
                query=self.get_query_argument("q", ""),
                sandbox_override=sandbox_override,
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


class ZenodoMeHandler(APIHandler):
    def initialize(self, zenodo_requests: ZenodoRequests):
        self.zenodo_requests = zenodo_requests

    @tornado.web.authenticated
    def get(self):
        token_id = _get_user_token_id(self)

        try:
            profile = self.zenodo_requests.get_zenodo_me(token_id)
        except ValueError as error:
            self.set_status(401)
            self.finish(json.dumps({"message": str(error)}))
            return
        except KeyError as error:
            self.set_status(502)
            self.finish(
                json.dumps({"message": f"Missing field in Zenodo profile: {error}"})
            )
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(profile))


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
    def initialize(self, zenodo_requests: ZenodoRequests):
        self.zenodo_requests = zenodo_requests

    @tornado.web.authenticated
    def get(self):
        token_id = _get_user_token_id(self)

        sandbox_override = None
        if self.get_query_argument("sandbox", None) is not None:
            sandbox_override = self.get_query_argument("sandbox", "false").lower() in (
                "1",
                "true",
            )

        try:
            depositions = self.zenodo_requests.list_zenodo_depositions(
                token_id,
                sandbox_override=sandbox_override,
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
    zenodo_requests = ZenodoRequests(token_store)

    zenodo_base_url = url_path_join(base_url, "zenodo-jupyterlab")
    handlers = [
        (url_path_join(zenodo_base_url, "hello"), HelloRouteHandler),
        (
            url_path_join(zenodo_base_url, "access-token"),
            ZenodoAccessTokenHandler,
            {"zenodo_requests": zenodo_requests},
        ),
        (
            url_path_join(zenodo_base_url, "records"),
            ZenodoRecordsHandler,
            {"zenodo_requests": zenodo_requests},
        ),
        (
            url_path_join(zenodo_base_url, "me"),
            ZenodoMeHandler,
            {"zenodo_requests": zenodo_requests},
        ),
        (url_path_join(zenodo_base_url, "whoami"), WhoAmIHandler),
        (
            url_path_join(zenodo_base_url, "depositions"),
            ZenodoDepositionsHandler,
            {"zenodo_requests": zenodo_requests},
        ),
    ]

    web_app.add_handlers(host_pattern, handlers)
