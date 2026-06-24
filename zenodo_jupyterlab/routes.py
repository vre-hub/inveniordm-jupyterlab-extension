import json
import os
from pathlib import Path
from typing import Callable

from jupyter_server.base.handlers import APIHandler
from jupyter_core.paths import jupyter_data_dir
from jupyter_server.utils import url_path_join
import tornado
import requests

from .cell_actions import make_zenodo_import_cell_action
from .download_job_manager import DownloadJobManager
from .download_manager import DownloadManager
from .token_store import FileTokenStore
from .zenodo_requests import ZenodoRequests


GetZenodoRequests = Callable[[APIHandler], ZenodoRequests]
GetDownloadManager = Callable[[], DownloadManager]
GetDownloadJobManager = Callable[[], DownloadJobManager]


def _default_token_store_path() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "tokens.json"


def _default_downloads_dir() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "downloads"


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


def _get_sandbox_override(handler: APIHandler) -> bool | None:
    if handler.get_query_argument("sandbox", None) is None:
        return None

    return handler.get_query_argument("sandbox", "false").lower() in ("1", "true")


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
    def initialize(self, get_zenodo_requests: GetZenodoRequests):
        self.get_zenodo_requests = get_zenodo_requests

    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        status = self.get_zenodo_requests(self).get_access_token_status()
        self.finish(json.dumps(status.__dict__))

    @tornado.web.authenticated
    def put(self):
        data = self.get_json_body() or {}
        access_token = data.get("access_token")
        if not access_token:
            self.set_status(400)
            self.finish(json.dumps({"message": "Missing 'access_token' in request body"}))
            return

        access_token_valid = self.get_zenodo_requests(self).set_access_token(
            access_token
        )
        if not access_token_valid:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid Zenodo access token"}))
            return

        self.finish(json.dumps({"message": "Access token received successfully"}))

    @tornado.web.authenticated
    def delete(self):
        self.get_zenodo_requests(self).remove_access_token()
        self.finish(json.dumps({"message": "Access token removed successfully"}))


class ZenodoRecordsHandler(APIHandler):
    def initialize(self, get_zenodo_requests: GetZenodoRequests):
        self.get_zenodo_requests = get_zenodo_requests

    @tornado.web.authenticated
    def get(self):
        filters = {
            key: self.get_query_argument(key, None)
            for key in ("communities", "type", "subtype", "bounds", "custom")
        }
        filters = {key: value for key, value in filters.items() if value}
        include_files = self.get_query_argument("include_files", "false").lower() in (
            "1",
            "true",
        )

        try:
            # TODO refactor so we do not specify defaults twice (here and in zenodo.py)
            records = self.get_zenodo_requests(self).search_zenodo_records(
                query=self.get_query_argument("q", ""),
                page=int(self.get_query_argument("page", "1")),
                size=int(self.get_query_argument("size", "10")),
                sort=self.get_query_argument("sort", "bestmatch"),
                all_versions=self.get_query_argument("all_versions", "false").lower()
                in ("1", "true"),
                filters=filters,
                include_files=include_files,
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
    def initialize(self, get_zenodo_requests: GetZenodoRequests):
        self.get_zenodo_requests = get_zenodo_requests

    @tornado.web.authenticated
    def get(self):
        try:
            profile = self.get_zenodo_requests(self).get_zenodo_me()
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
    def initialize(self, get_zenodo_requests: GetZenodoRequests):
        self.get_zenodo_requests = get_zenodo_requests

    @tornado.web.authenticated
    def get(self):
        include_files = self.get_query_argument("include_files", "false").lower() in (
            "1",
            "true",
        )

        try:
            depositions = self.get_zenodo_requests(self).list_zenodo_depositions(
                page=int(self.get_query_argument("page", "1")),
                size=int(self.get_query_argument("size", "10")),
                include_files=include_files,
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


class ZenodoFileDownloadHandler(APIHandler):
    def initialize(
        self,
        get_zenodo_requests: GetZenodoRequests,
        get_download_manager: GetDownloadManager,
        get_download_job_manager: GetDownloadJobManager,
    ):
        self.get_zenodo_requests = get_zenodo_requests
        self.get_download_manager = get_download_manager
        self.get_download_job_manager = get_download_job_manager

    @tornado.web.authenticated
    def post(self):
        data = self.get_json_body() or {}
        deposition_id = data.get("deposition_id")
        file_id = data.get("file_id")
        if deposition_id is None or not file_id:
            self.set_status(400)
            self.finish(
                json.dumps({"message": "Missing deposition_id or file_id"})
            )
            return

        zenodo_requests = self.get_zenodo_requests(self)
        download_manager = self.get_download_manager()
        download_id = self.get_download_job_manager().start_download(
            lambda on_progress, should_cancel: download_manager.download_zenodo_file(
                zenodo_requests,
                deposition_id=deposition_id,
                file_id=file_id,
                on_progress=on_progress,
                should_cancel=should_cancel,
            )
        )
        self.finish(json.dumps({"download_id": download_id}))


class ZenodoDownloadProgressHandler(APIHandler):
    def initialize(self, get_download_job_manager: GetDownloadJobManager):
        self.get_download_job_manager = get_download_job_manager

    @tornado.web.authenticated
    def get(self, download_id: str):
        progress = self.get_download_job_manager().get_progress(download_id)
        if progress is None:
            self.set_status(404)
            self.finish(json.dumps({"message": "Unknown download"}))
            return

        self.finish(json.dumps(progress))


class ZenodoDownloadCancelHandler(APIHandler):
    def initialize(self, get_download_job_manager: GetDownloadJobManager):
        self.get_download_job_manager = get_download_job_manager

    @tornado.web.authenticated
    def post(self, download_id: str):
        progress = self.get_download_job_manager().cancel(download_id)
        if progress is None:
            self.set_status(404)
            self.finish(json.dumps({"message": "Unknown download"}))
            return

        self.finish(json.dumps(progress))


class ZenodoFileImportCellHandler(APIHandler):
    def initialize(
        self,
        get_zenodo_requests: GetZenodoRequests,
        get_download_manager: GetDownloadManager,
    ):
        self.get_zenodo_requests = get_zenodo_requests
        self.get_download_manager = get_download_manager

    @tornado.web.authenticated
    def post(self):
        data = self.get_json_body() or {}
        deposition_id = data.get("deposition_id")
        file_id = data.get("file_id")
        framework = data.get("framework", "pandas")
        if deposition_id is None or not file_id:
            self.set_status(400)
            self.finish(
                json.dumps({"message": "Missing deposition_id or file_id"})
            )
            return

        try:
            destination = self.get_download_manager().get_zenodo_download_location(
                self.get_zenodo_requests(self),
                deposition_id=deposition_id,
                file_id=file_id,
            )
            if not destination.exists():
                raise ValueError("Zenodo file has not been downloaded yet")
            action = make_zenodo_import_cell_action(
                path=destination,
                deposition_id=deposition_id,
                file_id=file_id,
                framework=framework,
            )
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(action))


def setup_route_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    token_store = FileTokenStore(_default_token_store_path())
    download_job_manager = DownloadJobManager()

    def get_zenodo_requests(handler: APIHandler) -> ZenodoRequests:
        return ZenodoRequests(
            token_store,
            token_id=_get_user_token_id(handler),
            sandbox_override=_get_sandbox_override(handler),
        )

    def get_download_manager() -> DownloadManager:
        return DownloadManager(_default_downloads_dir())

    def get_download_job_manager() -> DownloadJobManager:
        return download_job_manager

    zenodo_base_url = url_path_join(base_url, "zenodo-jupyterlab")
    handlers = [
        (url_path_join(zenodo_base_url, "hello"), HelloRouteHandler),
        (
            url_path_join(zenodo_base_url, "access-token"),
            ZenodoAccessTokenHandler,
            {"get_zenodo_requests": get_zenodo_requests},
        ),
        (
            url_path_join(zenodo_base_url, "records"),
            ZenodoRecordsHandler,
            {"get_zenodo_requests": get_zenodo_requests},
        ),
        (
            url_path_join(zenodo_base_url, "me"),
            ZenodoMeHandler,
            {"get_zenodo_requests": get_zenodo_requests},
        ),
        (url_path_join(zenodo_base_url, "whoami"), WhoAmIHandler),
        (
            url_path_join(zenodo_base_url, "depositions"),
            ZenodoDepositionsHandler,
            {"get_zenodo_requests": get_zenodo_requests},
        ),
        (
            url_path_join(zenodo_base_url, "files", "download"),
            ZenodoFileDownloadHandler,
            {
                "get_zenodo_requests": get_zenodo_requests,
                "get_download_manager": get_download_manager,
                "get_download_job_manager": get_download_job_manager,
            },
        ),
        (
            url_path_join(
                zenodo_base_url,
                "files",
                "downloads",
                r"([^/]+)",
                "progress",
            ),
            ZenodoDownloadProgressHandler,
            {"get_download_job_manager": get_download_job_manager},
        ),
        (
            url_path_join(
                zenodo_base_url,
                "files",
                "downloads",
                r"([^/]+)",
                "cancel",
            ),
            ZenodoDownloadCancelHandler,
            {"get_download_job_manager": get_download_job_manager},
        ),
        (
            url_path_join(zenodo_base_url, "files", "import-cell"),
            ZenodoFileImportCellHandler,
            {
                "get_zenodo_requests": get_zenodo_requests,
                "get_download_manager": get_download_manager,
            },
        ),
    ]

    web_app.add_handlers(host_pattern, handlers)
