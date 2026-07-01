import json
import os
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from jupyter_server.base.handlers import APIHandler
from jupyter_core.paths import jupyter_data_dir
from jupyter_server.utils import url_path_join
import tornado
import requests

from .cell_actions import make_zenodo_import_cell_action
from .zenodo_download_manager import ZenodoDownloadManager
from .zenodo_requests.zenodo_requests import ZenodoRequests
from .zenodo_requests.zenodo_requests_factory import ZenodoRequestsFactory
from .zenodo_requests.zenodo_requests_factory_create import (
    create_zenodo_requests_factory,
)

from .util.sse import EventBus, stream_user_events

GetZenodoRequests = Callable[[APIHandler], ZenodoRequests]
GetZenodoDownloadManager = Callable[[], ZenodoDownloadManager]



def get_user_id(handler: APIHandler) -> str:
    """
    Get a unique ID for the current user.
    """
    return handler.current_user.username

def _default_downloads_dir() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "downloads"


def _download_status_changed_topic(deposition_id: int | str, file_id: str) -> str:
    return (
        "file.download-status.changed."
        f"{quote(str(deposition_id), safe='')}."
        f"{quote(file_id, safe='')}"
    )


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
    def initialize(
        self,
        zenodo_requests_factory: ZenodoRequestsFactory,
        event_bus: EventBus,
    ):
        self.zenodo_requests_factory = zenodo_requests_factory
        self.event_bus = event_bus

    def _publish_access_token_status(self) -> None:
        """
        Notify the frontend that the access token status has changed
        (e.g. after a token has been added or removed).
        """
        self.event_bus.publish(
            self.current_user.username,
            "auth.status.changed",
        )

    @tornado.web.authenticated
    def get(self):
        status = self.zenodo_requests_factory.get_access_token_status(self)
        self.finish(json.dumps(status.__dict__))

    @tornado.web.authenticated
    def put(self):
        try:
            self.zenodo_requests_factory.put_access_token(self)
        except NotImplementedError as error:
            self.set_status(501)
            self.finish(json.dumps({"message": str(error)}))
            return
        self._publish_access_token_status()

    @tornado.web.authenticated
    def delete(self):
        try:
            self.zenodo_requests_factory.delete_access_token(self)
        except NotImplementedError as error:
            self.set_status(501)
            self.finish(json.dumps({"message": str(error)}))
            return
        self._publish_access_token_status()


class ZenodoAuthHandler(APIHandler):
    def initialize(self, zenodo_requests_factory: ZenodoRequestsFactory):
        self.zenodo_requests_factory = zenodo_requests_factory

    @tornado.web.authenticated
    def get(self, action: str):
        try:
            self.zenodo_requests_factory.handle_auth(self, action)
        except NotImplementedError as error:
            self.set_status(501)
            self.finish(json.dumps({"message": str(error)}))


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


class ZenodoEventsHandler(APIHandler):
    def initialize(
        self,
        event_bus: EventBus,
    ):
        self.event_bus = event_bus

    @tornado.web.authenticated
    async def get(self):
        """
        Allow clients to subscribe to all SSE events for the current user.
        The connection will be kept open and events will be sent as they occur.
        """
        await stream_user_events(
            self,
            event_bus=self.event_bus,
            user_id=get_user_id(self),
        )


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
        get_zenodo_download_manager: GetZenodoDownloadManager,
        event_bus: EventBus,
    ):
        self.get_zenodo_requests = get_zenodo_requests
        self.get_zenodo_download_manager = get_zenodo_download_manager
        self.event_bus = event_bus

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
        user_id = get_user_id(self)

        def publish_download_progress(
            download_id: str,
            progress: dict[str, object],
        ) -> None:
            self.event_bus.publish(
                user_id,
                f"download.progress.{download_id}",
                progress,
            )
            if progress.get("status") == "done":
                self.event_bus.publish(
                    user_id,
                    _download_status_changed_topic(deposition_id, file_id),
                )

        download_id = self.get_zenodo_download_manager().start_download(
            zenodo_requests,
            deposition_id=deposition_id,
            file_id=file_id,
            on_progress_changed=publish_download_progress,
        )
        self.finish(json.dumps({"download_id": download_id}))

    @tornado.web.authenticated
    def delete(self):
        data = self.get_json_body() or {}
        deposition_id = data.get("deposition_id")
        file_id = data.get("file_id")
        if deposition_id is None or not file_id:
            self.set_status(400)
            self.finish(
                json.dumps({"message": "Missing deposition_id or file_id"})
            )
            return

        try:
            result = self.get_zenodo_download_manager().delete_download(
                deposition_id=deposition_id,
                file_id=file_id,
            )
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return

        if result.get("deleted"):
            self.event_bus.publish(
                get_user_id(self),
                _download_status_changed_topic(deposition_id, file_id),
            )

        self.finish(json.dumps(result))


class ZenodoDownloadCancelHandler(APIHandler):
    def initialize(self, get_zenodo_download_manager: GetZenodoDownloadManager):
        self.get_zenodo_download_manager = get_zenodo_download_manager

    @tornado.web.authenticated
    def post(self, download_id: str):
        progress = self.get_zenodo_download_manager().cancel(download_id)
        if progress is None:
            self.set_status(404)
            self.finish(json.dumps({"message": "Unknown download"}))
            return

        self.finish(json.dumps(progress))


class ZenodoFileDownloadStatusHandler(APIHandler):
    def initialize(self, get_zenodo_download_manager: GetZenodoDownloadManager):
        self.get_zenodo_download_manager = get_zenodo_download_manager

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

        try:
            status = self.get_zenodo_download_manager().get_download_status(
                deposition_id=deposition_id,
                file_id=file_id,
            )
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(status))


class ZenodoFileImportCellHandler(APIHandler):
    def initialize(
        self,
        get_zenodo_requests: GetZenodoRequests,
        get_zenodo_download_manager: GetZenodoDownloadManager,
    ):
        self.get_zenodo_requests = get_zenodo_requests
        self.get_zenodo_download_manager = get_zenodo_download_manager

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

        try:
            zenodo_requests = self.get_zenodo_requests(self)
            destination = self.get_zenodo_download_manager().get_download_location(
                zenodo_requests,
                deposition_id=deposition_id,
                file_id=file_id,
            )
            if not destination.exists():
                raise ValueError("Zenodo file has not been downloaded yet")
            file_metadata = zenodo_requests.get_zenodo_deposition_file(
                deposition_id=deposition_id,
                file_id=file_id,
            )
            action = make_zenodo_import_cell_action(
                path=destination,
                deposition_id=deposition_id,
                file_id=file_id,
                file_metadata=file_metadata,
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
    event_bus = EventBus()
    zenodo_download_manager = ZenodoDownloadManager(_default_downloads_dir())
    zenodo_requests_factory = create_zenodo_requests_factory()

    def get_zenodo_requests(handler: APIHandler) -> ZenodoRequests:
        return zenodo_requests_factory.create_zenodo_requests(handler)

    def get_zenodo_download_manager() -> ZenodoDownloadManager:
        return zenodo_download_manager

    zenodo_base_url = url_path_join(base_url, "zenodo-jupyterlab")
    handlers = [
        (url_path_join(zenodo_base_url, "hello"), HelloRouteHandler),
        (
            url_path_join(zenodo_base_url, "access-token"),
            ZenodoAccessTokenHandler,
            {
                "zenodo_requests_factory": zenodo_requests_factory,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(zenodo_base_url, "auth", r"(login|logout)"),
            ZenodoAuthHandler,
            {"zenodo_requests_factory": zenodo_requests_factory},
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
        (
            url_path_join(zenodo_base_url, "events"),
            ZenodoEventsHandler,
            {"event_bus": event_bus},
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
                "get_zenodo_download_manager": get_zenodo_download_manager,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(zenodo_base_url, "files", "status"),
            ZenodoFileDownloadStatusHandler,
            {"get_zenodo_download_manager": get_zenodo_download_manager},
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
            {"get_zenodo_download_manager": get_zenodo_download_manager},
        ),
        (
            url_path_join(zenodo_base_url, "files", "import-cell"),
            ZenodoFileImportCellHandler,
            {
                "get_zenodo_requests": get_zenodo_requests,
                "get_zenodo_download_manager": get_zenodo_download_manager,
            },
        ),
    ]

    web_app.add_handlers(host_pattern, handlers)
