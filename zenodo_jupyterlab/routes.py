import json
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from jupyter_server.base.handlers import APIHandler
from jupyter_core.paths import jupyter_data_dir
from jupyter_server.utils import url_path_join
import tornado
import requests

from zenodo_jupyterlab.user_settings import ZenodoUserSettingsFromFile, ZenodoUserSettings
from zenodo_jupyterlab.util.download_job_manager import DownloadJobManager

from .cell_actions import make_zenodo_import_cell_action
from .zenodo_auth.auth_controller import ZenodoAuthController
from .zenodo_download_manager import ZenodoDownloadManager
from .zenodo_requests.zenodo_requests import ZenodoRequests
from .zenodo_requests.zenodo_requests_factory import ZenodoRequestsFactory
from .zenodo_requests.zenodo_requests_factory_create import (
    create_zenodo_requests_factory,
)

from .util.sse import EventBus, stream_user_events

GetZenodoRequests = Callable[[APIHandler], ZenodoRequests]
GetZenodoDownloadManager = Callable[[APIHandler], ZenodoDownloadManager]
GetUserSettings = Callable[[APIHandler], ZenodoUserSettings]


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
    ):
        self.zenodo_requests_factory = zenodo_requests_factory

    @tornado.web.authenticated
    def get(self):
        status = self.zenodo_requests_factory.get_access_token_status(self)
        self.finish(json.dumps(status.__dict__))


class ZenodoAuthHandler(APIHandler):
    def initialize(self, zenodo_auth_controller: ZenodoAuthController):
        self.zenodo_auth_controller = zenodo_auth_controller

    @tornado.web.authenticated
    def get(self, action: str):
        if action == "login":
            self.zenodo_auth_controller.login(self)
            return

        if action == "logout":
            self.zenodo_auth_controller.logout(self)
            return

        if action == "callback":
            self.zenodo_auth_controller.callback(self)
            return

        self.set_status(404)
        self.finish(json.dumps({"message": "Unknown auth action"}))


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

        download_id = self.get_zenodo_download_manager(self).start_download(
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
            result = self.get_zenodo_download_manager(self).delete_download(
                self.get_zenodo_requests(self),
                deposition_id=deposition_id,
                file_id=file_id,
            )
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
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
        progress = self.get_zenodo_download_manager(self).cancel(download_id)
        if progress is None:
            self.set_status(404)
            self.finish(json.dumps({"message": "Unknown download"}))
            return

        self.finish(json.dumps(progress))


class ZenodoFileDownloadStatusHandler(APIHandler):
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
            status = self.get_zenodo_download_manager(self).get_download_status(
                self.get_zenodo_requests(self),
                deposition_id=deposition_id,
                file_id=file_id,
            )
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
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
            destination = self.get_zenodo_download_manager(self).get_download_location(
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


class ZenodoDownloadLocationSettingHandler(APIHandler):

    def initialize(self, get_user_settings: GetUserSettings):
        self.get_user_settings = get_user_settings

    @tornado.web.authenticated
    def get(self):
        """
        Get the current downloads directory.
        """
        downloads_dir = self.get_user_settings(self).get_downloads_directory()
        self.finish(json.dumps({"downloads_dir": str(downloads_dir)}))

    @tornado.web.authenticated
    def post(self):
        """
        Set the downloads directory.
        """
        data = self.get_json_body() or {}
        downloads_dir = data.get("downloads_dir")
        if not downloads_dir:
            self.set_status(400)
            self.finish(json.dumps({"message": "Missing downloads_dir"}))
            return

        try:
            self.get_user_settings(self).set_downloads_directory(downloads_dir)
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps({"downloads_dir": str(self.get_user_settings(self).get_downloads_directory())}))

    @tornado.web.authenticated
    def delete(self):
        """
        Unset the configured downloads directory.
        """
        self.get_user_settings(self).unset_downloads_directory()
        self.finish(json.dumps({"downloads_dir": str(self.get_user_settings(self).get_downloads_directory())}))

def setup_route_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    event_bus = EventBus()
    download_job_manager = DownloadJobManager()
    zenodo_requests_factory = create_zenodo_requests_factory("local")

    def get_zenodo_requests(handler: APIHandler) -> ZenodoRequests:
        return zenodo_requests_factory.create_zenodo_requests(handler)

    def get_user_settings(handler: APIHandler) -> ZenodoUserSettings:
        contents_manager = handler.settings["contents_manager"]
        root_dir = Path(contents_manager.root_dir)
        return ZenodoUserSettingsFromFile(root_dir)

    def get_zenodo_download_manager(handler: APIHandler) -> ZenodoDownloadManager:
        settings = get_user_settings(handler)
        return ZenodoDownloadManager(settings.get_downloads_directory(), download_job_manager=download_job_manager)

    zenodo_base_url = url_path_join(base_url, "zenodo-jupyterlab")
    handlers = [
        (url_path_join(zenodo_base_url, "hello"), HelloRouteHandler),
        (
            url_path_join(zenodo_base_url, "access-token"),
            ZenodoAccessTokenHandler,
            {"zenodo_requests_factory": zenodo_requests_factory},
        ),
        (
            url_path_join(zenodo_base_url, "auth", r"(login|logout|callback)"),
            ZenodoAuthHandler,
            {"zenodo_auth_controller": zenodo_requests_factory.auth_controller},
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
            {
                "get_zenodo_requests": get_zenodo_requests,
                "get_zenodo_download_manager": get_zenodo_download_manager,
            },
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
        (
            url_path_join(zenodo_base_url, "settings", "downloads-directory"),
            ZenodoDownloadLocationSettingHandler,
            {"get_user_settings": get_user_settings},
        ),
    ]

    web_app.add_handlers(host_pattern, handlers)
