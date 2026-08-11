import asyncio
import json
from pathlib import Path
from typing import Callable, cast
from urllib.parse import quote

import requests
import tornado
from jupyter_core.paths import jupyter_data_dir
from jupyter_server.base.handlers import APIHandler as JupyterAPIHandler
from jupyter_server.utils import url_path_join

from zenodo_auth.remote_servers import RemoteServerRegistry, UnknownRemoteServerError
from zenodo_jupyterlab.user_settings import (
    ZenodoUserSettings,
    ZenodoUserSettingsFromFile,
)
from zenodo_jupyterlab.util.job_manager import JobContext, JobManager
from zenodo_jupyterlab.util.job_types import JobProgress

from .cell_actions import make_zenodo_import_cell_action
from .util.sse import EventBus, stream_user_events
from .zenodo_auth.auth_controller import ZenodoAuthController
from .zenodo_download_manager import ZenodoDownloadManager
from .zenodo_file_identifier import (
    ZenodoFileIdentifier,
    zenodo_file_identifier,
)
from .zenodo_record_identifier import (
    ZenodoRecordIdentifier,
    ZenodoRecordStatus,
    zenodo_record_identifier,
)
from .zenodo_requests.zenodo_requests import ZenodoRequests
from .zenodo_requests.zenodo_requests_factory import ZenodoRequestsFactory
from .zenodo_requests.zenodo_requests_factory_create import (
    create_zenodo_requests_factory,
)


class APIHandler(JupyterAPIHandler):
    def write_error(self, status_code: int, **kwargs) -> None:
        exc_info = kwargs.get("exc_info")
        if exc_info and isinstance(exc_info[1], UnknownRemoteServerError):
            self.set_status(400)
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps({"message": str(exc_info[1])}))
            return
        super().write_error(status_code, **kwargs)


GetZenodoRequests = Callable[[APIHandler], ZenodoRequests]
GetZenodoDownloadManager = Callable[[APIHandler], ZenodoDownloadManager]
GetJobManager = Callable[[APIHandler], JobManager]
CreateJobMetadata = Callable[[ZenodoRequests], dict[str, object]]
GetUserSettings = Callable[[APIHandler], ZenodoUserSettings]


def _contents_root(handler: APIHandler) -> Path:
    contents_manager = handler.settings["contents_manager"]
    return Path(contents_manager.root_dir).resolve()


def _resolve_contents_file_paths(
    handler: APIHandler,
    file_paths: list[str],
) -> list[Path]:
    """
    Convert a list of file paths that are relative to the Jupyter root into absolute paths on the filesystem.
    """
    root_dir = _contents_root(handler)
    resolved_paths = []

    for file_path in file_paths:
        path = (root_dir / file_path).resolve()
        if not path.is_relative_to(root_dir):
            raise ValueError(f"File is outside the Jupyter root: {file_path}")
        if not path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        resolved_paths.append(path)

    return resolved_paths


def get_user_id(handler: APIHandler) -> str:
    """
    Get a unique ID for the current user.
    """
    return handler.current_user.username


def _default_downloads_dir() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "downloads"


def _download_status_changed_topic(file_id: ZenodoFileIdentifier) -> str:
    return (
        "file.download-status.changed."
        f"{quote(str(file_id.record_id), safe='')}."
        f"{quote(file_id.record_status, safe='')}."
        f"{quote(file_id.file_key, safe='')}"
    )


def _record_changed_topic(record_id: int | str) -> str:
    return f"record.changed.{quote(str(record_id), safe='')}"


class HelloRouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps(
                {
                    "data": (
                        "Hello, world!"
                        " This is the '/zenodo-jupyterlab/hello' endpoint."
                        " Try visiting me in your browser!"
                    ),
                }
            )
        )


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


class ZenodoRemoteServersHandler(APIHandler):
    def initialize(self, remote_servers: RemoteServerRegistry):
        self.remote_servers = remote_servers

    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps(
                [
                    {
                        "id": server.id,
                        "label": server.label,
                    }
                    for server in self.remote_servers.all()
                ]
            )
        )


class ZenodoRemoteServersDefaultHandler(APIHandler):
    def initialize(self, remote_servers: RemoteServerRegistry):
        self.remote_servers = remote_servers

    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps(
                {
                    "id": self.remote_servers.default.id,
                    "label": self.remote_servers.default.label,
                }
            )
        )


class ZenodoCurrentRemoteServerHandler(APIHandler):
    def initialize(
        self,
        zenodo_requests_factory: ZenodoRequestsFactory,
    ):
        self.zenodo_requests_factory = zenodo_requests_factory

    @tornado.web.authenticated
    def get(self):
        zenodo_requests = self.zenodo_requests_factory.create_zenodo_requests(self)
        remote_server_id = self.zenodo_requests_factory.get_remote_server_id(
            zenodo_requests
        )
        remote_server = self.zenodo_requests_factory.remote_servers.get(
            remote_server_id
        )
        self.finish(
            json.dumps(
                {
                    "id": remote_server.id,
                    "display_name": remote_server.label,
                }
            )
        )


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


class ZenodoRecordCollectionHandler(APIHandler):
    def initialize(self, get_zenodo_requests: GetZenodoRequests):
        self.get_zenodo_requests = get_zenodo_requests

    @tornado.web.authenticated
    def get(self):
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
                allversions=self.get_query_argument("allversions", "false").lower()
                in ("1", "true"),
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


class ZenodoRecordVariantItemHandler(APIHandler):
    def initialize(self, get_zenodo_requests: GetZenodoRequests):
        self.get_zenodo_requests = get_zenodo_requests

    @tornado.web.authenticated
    def get(self, record_id: str):
        record_identifier = zenodo_record_identifier(
            record_id,
            self.get_query_argument("record_status", None),
        )
        if record_identifier is None:
            self.set_status(400)
            self.finish(
                json.dumps({"message": "record_status must be 'draft' or 'published'"})
            )
            return

        try:
            record = self.get_zenodo_requests(self).get_zenodo_record_variant(
                record_identifier
            )
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(record))


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


class ZenodoUserRecordCollectionHandler(APIHandler):
    def initialize(self, get_zenodo_requests: GetZenodoRequests):
        self.get_zenodo_requests = get_zenodo_requests

    @tornado.web.authenticated
    def get(self):
        include_files = self.get_query_argument("include_files", "false").lower() in (
            "1",
            "true",
        )

        try:
            records = self.get_zenodo_requests(self).list_zenodo_user_records(
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

        self.finish(json.dumps(records))


class ZenodoUserRecordItemHandler(APIHandler):
    def initialize(
        self,
        get_zenodo_requests: GetZenodoRequests,
        event_bus: EventBus,
    ):
        self.get_zenodo_requests = get_zenodo_requests
        self.event_bus = event_bus

    @tornado.web.authenticated
    def delete(self, record_id: str):
        try:
            zenodo_requests = self.get_zenodo_requests(self)
            # TODO check if we even need this api call and remove if we dont
            record = zenodo_requests.get_zenodo_record_variant(
                ZenodoRecordIdentifier(
                    record_id=record_id,
                    record_status="draft",
                )
            )
            parent_id_value = (record.get("parent") or {}).get("id")
            parent_id = str(parent_id_value) if parent_id_value else None
            versions = zenodo_requests.list_zenodo_record_versions(
                record_id, include_drafts=True
            )
            zenodo_requests.delete_zenodo_record_draft(record_id)
        except ValueError as error:
            self.set_status(401)
            self.finish(json.dumps({"message": str(error)}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.event_bus.publish(
            get_user_id(self),
            "record.versions.changed",
            {
                "type": "draft_discarded",
                "record_id": record_id,
                "discarded_draft_id": record_id,
                "parent_id": parent_id,
                "versions": [
                    version
                    for version in versions
                    if not (
                        str(version.get("id")) == str(record_id)
                        and version.get("is_draft", False) is True
                    )
                ],
            },
        )
        self.set_status(204)
        self.finish()


class ZenodoRecordPermissionHandler(APIHandler):
    def initialize(self, get_zenodo_requests: GetZenodoRequests):
        self.get_zenodo_requests = get_zenodo_requests

    @tornado.web.authenticated
    async def get(self, record_id: str):
        record_status = self.get_query_argument("record_status", None)
        if record_status not in {"draft", "published"}:
            self.set_status(400)
            self.finish(
                json.dumps({"message": "record_status must be 'draft' or 'published'"})
            )
            return

        try:
            zenodo_requests = self.get_zenodo_requests(self)
            permission = await asyncio.to_thread(
                zenodo_requests.get_zenodo_record_permission,
                record_id,
                cast(ZenodoRecordStatus, record_status),
            )  # run this in a thread until we have a proper async implementation of the api calls
        except ValueError as error:
            self.set_status(
                401
                if str(error) == "Missing Zenodo request authentication headers"
                else 404
            )
            self.finish(json.dumps({"message": str(error)}))
            return
        except (KeyError, TypeError) as error:
            self.set_status(502)
            self.finish(json.dumps({"message": f"Invalid Zenodo response: {error}"}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(permission))


class ZenodoRecordVersionCollectionHandler(APIHandler):
    def initialize(
        self,
        get_zenodo_requests: GetZenodoRequests,
        event_bus: EventBus,
    ):
        self.get_zenodo_requests = get_zenodo_requests
        self.event_bus = event_bus

    @tornado.web.authenticated
    async def get(self, record_id: str):
        include_drafts = self.get_query_argument("include_drafts", "true").lower() in (
            "1",
            "true",
        )
        try:
            versions = await asyncio.to_thread(
                self.get_zenodo_requests(self).list_zenodo_record_versions,
                record_id,
                include_drafts=include_drafts,
            )  # run this in a thread until we have a proper async implementation of the api calls
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(versions))

    @tornado.web.authenticated
    def post(self, record_id: str):
        try:
            zenodo_requests = self.get_zenodo_requests(self)
            versions = zenodo_requests.list_zenodo_record_versions(
                record_id, include_drafts=True
            )
            draft = zenodo_requests.create_zenodo_record_version(record_id)
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        draft_id = str(draft.get("id"))
        corrected_versions = [
            version
            for version in versions
            if not (
                str(version.get("id")) == draft_id
                and version.get("is_draft", False) is True
            )
        ]
        corrected_versions.append(draft)
        parent_id_value = (draft.get("parent") or {}).get("id")
        self.event_bus.publish(
            get_user_id(self),
            "record.versions.changed",
            {
                "type": "version_created",
                "record_id": record_id,
                "parent_id": (str(parent_id_value) if parent_id_value else None),
                "record": draft,
                "versions": corrected_versions,
            },
        )
        self.finish(json.dumps({"draft": draft}))


class ZenodoRecordDraftWithFilesHandler(APIHandler):
    def initialize(
        self,
        get_zenodo_requests: GetZenodoRequests,
        get_job_manager: GetJobManager,
        event_bus: EventBus,
    ):
        self.get_zenodo_requests = get_zenodo_requests
        self.get_job_manager = get_job_manager
        self.event_bus = event_bus

    @tornado.web.authenticated
    def post(self):
        data = self.get_json_body() or {}
        file_paths = data.get("file_paths")

        if not isinstance(file_paths, list) or not file_paths:
            self.set_status(400)
            self.finish(json.dumps({"message": "Missing file_paths"}))
            return

        if not all(isinstance(file_path, str) for file_path in file_paths):
            self.set_status(400)
            self.finish(json.dumps({"message": "file_paths must be strings"}))
            return

        try:
            resolved_file_paths = _resolve_contents_file_paths(self, file_paths)
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return

        zenodo_requests = self.get_zenodo_requests(self)
        user_id = get_user_id(self)

        def publish_job_progress(
            job_id: str,
            progress: dict[str, object],
        ) -> None:
            self.event_bus.publish(
                user_id,
                f"job.progress.{job_id}",
                progress,
            )
            if progress.get("status") == "done":
                result = progress.get("result")
                draft = result.get("draft") if isinstance(result, dict) else None
                record_id = draft.get("id") if isinstance(draft, dict) else None
                if record_id is not None:
                    self.event_bus.publish(
                        user_id,
                        _record_changed_topic(record_id),
                    )

        def upload(context: JobContext) -> dict[str, object]:
            def on_upload_progress(
                bytes_uploaded: int,
                total_bytes: int,
                current_file: str | None,
            ) -> None:
                context.update(
                    completed_bytes=bytes_uploaded,
                    total_bytes=total_bytes,
                    current_item=current_file,
                )

            draft = zenodo_requests.create_zenodo_record_draft_with_files(
                file_paths=resolved_file_paths,
                on_upload_progress=on_upload_progress,
                should_cancel=context.should_cancel,
            )
            return {"draft": draft}

        job_id = self.get_job_manager(self).start(
            upload,
            progress=JobProgress(job_type="upload"),
            on_progress_changed=publish_job_progress,
            cancel_message="Upload canceled",
        )
        self.finish(json.dumps({"job_id": job_id}))


class ZenodoRecordFileCollectionHandler(APIHandler):
    def initialize(
        self,
        get_zenodo_requests: GetZenodoRequests,
        get_job_manager: GetJobManager,
        create_job_metadata: CreateJobMetadata,
        event_bus: EventBus,
    ):
        self.get_zenodo_requests = get_zenodo_requests
        self.get_job_manager = get_job_manager
        self.create_job_metadata = create_job_metadata
        self.event_bus = event_bus

    @tornado.web.authenticated
    def post(self, record_id: str):
        data = self.get_json_body() or {}
        file_paths = data.get("file_paths")

        if not isinstance(file_paths, list) or not file_paths:
            self.set_status(400)
            self.finish(json.dumps({"message": "Missing file_paths"}))
            return

        if not all(isinstance(file_path, str) for file_path in file_paths):
            self.set_status(400)
            self.finish(json.dumps({"message": "file_paths must be strings"}))
            return

        try:
            resolved_file_paths = _resolve_contents_file_paths(self, file_paths)
        except ValueError as error:
            self.set_status(400)
            self.finish(json.dumps({"message": str(error)}))
            return

        zenodo_requests = self.get_zenodo_requests(self)
        try:
            account_metadata = self.create_job_metadata(zenodo_requests)
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
        user_id = get_user_id(self)

        def publish_job_progress(
            job_id: str,
            progress: dict[str, object],
        ) -> None:
            self.event_bus.publish(
                user_id,
                f"job.progress.{job_id}",
                progress,
            )
            if progress.get("status") == "done":
                self.event_bus.publish(
                    user_id,
                    _record_changed_topic(record_id),
                )

        def upload(context: JobContext) -> dict[str, object]:
            def on_upload_progress(
                bytes_uploaded: int,
                total_bytes: int,
                current_file: str | None,
            ) -> None:
                context.update(
                    completed_bytes=bytes_uploaded,
                    total_bytes=total_bytes,
                    current_item=current_file,
                )

            zenodo_requests.upload_zenodo_record_files(
                record_id=record_id,
                file_paths=resolved_file_paths,
                on_upload_progress=on_upload_progress,
                should_cancel=context.should_cancel,
            )
            return {}

        job_id = self.get_job_manager(self).start(
            upload,
            progress=JobProgress(
                job_type="upload",
                metadata={
                    **account_metadata,
                    "record_id": str(record_id),
                },
            ),
            on_progress_changed=publish_job_progress,
            cancel_message="Upload canceled",
        )
        self.finish(json.dumps({"job_id": job_id}))

    @tornado.web.authenticated
    def delete(self, record_id: str):
        data = self.get_json_body() or {}
        file_id = zenodo_file_identifier(
            data.get("record_id"),
            data.get("record_status"),
            data.get("file_key"),
        )

        if file_id is None or str(file_id.record_id) != record_id:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        try:
            zenodo_requests = self.get_zenodo_requests(self)
            zenodo_requests.delete_zenodo_record_file(
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

        self.event_bus.publish(
            get_user_id(self),
            _record_changed_topic(record_id),
        )
        self.finish(json.dumps({"deleted_key": file_id.file_key}))


class JobsHandler(APIHandler):
    """
    Allows clients to list all jobs, optionally filtered by job type and status.
    Can be used to display e.g. download progress after page reload.
    """

    # TODO add SSE to notify clients of new jobs so that client does not have to keep track of the jobs it starts itself
    def initialize(
        self,
        get_job_manager: GetJobManager,
        get_zenodo_requests: GetZenodoRequests,
        create_job_metadata: CreateJobMetadata,
    ):
        self.get_job_manager = get_job_manager
        self.get_zenodo_requests = get_zenodo_requests
        self.create_job_metadata = create_job_metadata

    @tornado.web.authenticated
    def get(self):
        job_type = self.get_query_argument("job_type", None)
        status = self.get_query_argument("status", None)
        latest = self.get_query_argument("latest", "false").lower() in {
            "1",
            "true",
        }

        statuses = None
        if status == "active":
            statuses = {"pending", "running", "canceling"}
        elif status is not None:
            statuses = {status}

        metadata: dict[str, object] = {}
        record_id = self.get_query_argument("record_id", None)
        file_key = self.get_query_argument("file_key", None)
        record_status = self.get_query_argument("record_status", None)
        if record_id is not None:
            metadata["record_id"] = record_id
        if file_key is not None:
            metadata["file_key"] = file_key
        if record_status is not None:
            metadata["record_status"] = record_status

        if job_type == "upload":
            zenodo_requests = self.get_zenodo_requests(self)
            try:
                account_metadata = self.create_job_metadata(zenodo_requests)
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
            metadata.update(account_metadata)

        jobs = self.get_job_manager(self).find_progress(
            job_type=job_type,
            statuses=statuses,
            metadata=metadata,
        )
        if latest:
            jobs = jobs[:1]
        self.finish(json.dumps({"job_ids": [job["job_id"] for job in jobs]}))


class JobProgressHandler(APIHandler):
    def initialize(self, get_job_manager: GetJobManager):
        self.get_job_manager = get_job_manager

    @tornado.web.authenticated
    def get(self, job_id: str):
        progress = self.get_job_manager(self).get_progress(job_id)
        if progress is None:
            self.set_status(404)
            self.finish(json.dumps({"message": "Unknown job"}))
            return

        self.finish(json.dumps(progress))


class JobCancelHandler(APIHandler):
    def initialize(self, get_job_manager: GetJobManager):
        self.get_job_manager = get_job_manager

    @tornado.web.authenticated
    def post(self, job_id: str):
        progress = self.get_job_manager(self).cancel(job_id)
        if progress is None:
            self.set_status(404)
            self.finish(json.dumps({"message": "Unknown job"}))
            return

        self.finish(json.dumps(progress))


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
        record_id = data.get("record_id")
        record_status = data.get("record_status")
        file_key = data.get("file_key")
        file_id = zenodo_file_identifier(record_id, record_status, file_key)
        if file_id is None:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        zenodo_requests = self.get_zenodo_requests(self)
        user_id = get_user_id(self)

        def publish_job_progress(
            job_id: str,
            progress: dict[str, object],
        ) -> None:
            self.event_bus.publish(
                user_id,
                f"job.progress.{job_id}",
                progress,
            )
            if progress.get("status") == "done":
                self.event_bus.publish(
                    user_id,
                    _download_status_changed_topic(file_id),
                )

        job_id = self.get_zenodo_download_manager(self).start_download(
            zenodo_requests,
            file_id=file_id,
            on_progress_changed=publish_job_progress,
        )
        self.finish(json.dumps({"job_id": job_id}))

    @tornado.web.authenticated
    def delete(self):
        data = self.get_json_body() or {}
        record_id = data.get("record_id")
        record_status = data.get("record_status")
        file_key = data.get("file_key")
        file_id = zenodo_file_identifier(record_id, record_status, file_key)
        if file_id is None:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        try:
            result = self.get_zenodo_download_manager(self).delete_download(
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
                _download_status_changed_topic(file_id),
            )

        self.finish(json.dumps(result))


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
        record_id = data.get("record_id")
        record_status = data.get("record_status")
        file_key = data.get("file_key")
        file_id = zenodo_file_identifier(record_id, record_status, file_key)
        if file_id is None:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        try:
            status = self.get_zenodo_download_manager(self).get_download_status(
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
        record_id = data.get("record_id")
        record_status = data.get("record_status")
        file_key = data.get("file_key")
        file_id = zenodo_file_identifier(record_id, record_status, file_key)
        if file_id is None:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        try:
            destination = self.get_zenodo_download_manager(self).get_download_location(
                file_id=file_id,
            )
            if not destination.exists():
                raise ValueError("Zenodo file has not been downloaded yet")
            action = make_zenodo_import_cell_action(
                path=destination,
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

        self.finish(
            json.dumps(
                {
                    "downloads_dir": str(
                        self.get_user_settings(self).get_downloads_directory()
                    )
                }
            )
        )

    @tornado.web.authenticated
    def delete(self):
        """
        Unset the configured downloads directory.
        """
        self.get_user_settings(self).unset_downloads_directory()
        self.finish(
            json.dumps(
                {
                    "downloads_dir": str(
                        self.get_user_settings(self).get_downloads_directory()
                    )
                }
            )
        )


def setup_route_handlers(
    web_app,
    remote_servers: RemoteServerRegistry,
):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    event_bus = EventBus()
    job_manager = JobManager()
    zenodo_requests_factory = create_zenodo_requests_factory(
        remote_servers,
        "local",
    )

    def get_zenodo_requests(handler: APIHandler) -> ZenodoRequests:
        return zenodo_requests_factory.create_zenodo_requests(handler)

    def create_job_metadata(
        zenodo_requests: ZenodoRequests,
    ) -> dict[str, object]:
        return {
            "zenodo_user_id": zenodo_requests.zenodo_user_id,
            "remote_server_id": zenodo_requests_factory.get_remote_server_id(
                zenodo_requests
            ),
        }

    def get_user_settings(handler: APIHandler) -> ZenodoUserSettings:
        return ZenodoUserSettingsFromFile(_contents_root(handler))

    def get_zenodo_download_manager(handler: APIHandler) -> ZenodoDownloadManager:
        settings = get_user_settings(handler)
        zenodo_requests = get_zenodo_requests(handler)
        return ZenodoDownloadManager(
            settings.get_downloads_directory(),
            remote_server_id=zenodo_requests_factory.get_remote_server_id(
                zenodo_requests
            ),
            job_manager=job_manager,
        )

    def get_job_manager(handler: APIHandler) -> JobManager:
        return job_manager

    zenodo_base_url = url_path_join(base_url, "zenodo-jupyterlab")
    handlers = [
        (url_path_join(zenodo_base_url, "hello"), HelloRouteHandler),
        (
            url_path_join(zenodo_base_url, "access-token"),
            ZenodoAccessTokenHandler,
            {"zenodo_requests_factory": zenodo_requests_factory},
        ),
        (
            url_path_join(zenodo_base_url, "remote-servers"),
            ZenodoRemoteServersHandler,
            {"remote_servers": remote_servers},
        ),
        (
            url_path_join(zenodo_base_url, "remote-servers", "default"),
            ZenodoRemoteServersDefaultHandler,
            {"remote_servers": remote_servers},
        ),
        (
            url_path_join(zenodo_base_url, "remote-servers", "current"),
            ZenodoCurrentRemoteServerHandler,
            {"zenodo_requests_factory": zenodo_requests_factory},
        ),
        (
            url_path_join(zenodo_base_url, "auth", r"(login|logout|callback)"),
            ZenodoAuthHandler,
            {"zenodo_auth_controller": zenodo_requests_factory.auth_controller},
        ),
        (
            url_path_join(zenodo_base_url, "records"),
            ZenodoRecordCollectionHandler,
            {"get_zenodo_requests": get_zenodo_requests},
        ),
        (
            url_path_join(zenodo_base_url, "record-variants", r"([^/]+)"),
            ZenodoRecordVariantItemHandler,
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
            url_path_join(zenodo_base_url, "user", "records"),
            ZenodoUserRecordCollectionHandler,
            {"get_zenodo_requests": get_zenodo_requests},
        ),
        (
            url_path_join(
                zenodo_base_url,
                "user",
                "records",
                "draft-with-files",
            ),
            ZenodoRecordDraftWithFilesHandler,
            {
                "get_zenodo_requests": get_zenodo_requests,
                "get_job_manager": get_job_manager,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(
                zenodo_base_url,
                "records",
                r"([^/]+)",
                "versions",
            ),
            ZenodoRecordVersionCollectionHandler,
            {
                "get_zenodo_requests": get_zenodo_requests,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(
                zenodo_base_url,
                "records",
                r"([^/]+)",
                "permission",
            ),
            ZenodoRecordPermissionHandler,
            {"get_zenodo_requests": get_zenodo_requests},
        ),
        (
            url_path_join(zenodo_base_url, "user", "records", r"([^/]+)"),
            ZenodoUserRecordItemHandler,
            {
                "get_zenodo_requests": get_zenodo_requests,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(
                zenodo_base_url,
                "user",
                "records",
                r"([^/]+)",
                "files",
            ),
            ZenodoRecordFileCollectionHandler,
            {
                "get_zenodo_requests": get_zenodo_requests,
                "get_job_manager": get_job_manager,
                "create_job_metadata": create_job_metadata,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(zenodo_base_url, "jobs"),
            JobsHandler,
            {
                "get_job_manager": get_job_manager,
                "get_zenodo_requests": get_zenodo_requests,
                "create_job_metadata": create_job_metadata,
            },
        ),
        (
            url_path_join(
                zenodo_base_url,
                "jobs",
                r"([^/]+)",
                "cancel",
            ),
            JobCancelHandler,
            {"get_job_manager": get_job_manager},
        ),
        (
            url_path_join(zenodo_base_url, "jobs", r"([^/]+)"),
            JobProgressHandler,
            {"get_job_manager": get_job_manager},
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
