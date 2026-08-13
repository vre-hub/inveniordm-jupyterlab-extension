import asyncio
import json
from pathlib import Path
from typing import cast
from urllib.parse import quote

import requests
import tornado

from ..inveniordm_file_identifier import inveniordm_file_identifier
from ..inveniordm_record_identifier import (
    InvenioRDMRecordIdentifier,
    InvenioRDMRecordStatus,
    inveniordm_record_identifier,
)
from ..util.job_manager import JobContext
from ..util.job_types import JobProgress
from ..util.sse import EventBus
from .base import (
    APIHandler,
    CreateJobMetadata,
    GetInvenioRDMRequests,
    GetJobManager,
    contents_root,
    get_user_id,
)


def _record_changed_topic(record_id: int | str) -> str:
    return f"record.changed.{quote(str(record_id), safe='')}"


def _resolve_contents_file_paths(
    handler: APIHandler,
    file_paths: list[str],
) -> list[Path]:
    """
    Convert a list of file paths that are relative to the Jupyter root into absolute paths on the filesystem.
    """
    root_dir = contents_root(handler)
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


class InvenioRDMRecordCollectionHandler(APIHandler):
    def initialize(self, get_inveniordm_requests: GetInvenioRDMRequests):
        self.get_inveniordm_requests = get_inveniordm_requests

    @tornado.web.authenticated
    def get(self):
        include_files = self.get_query_argument("include_files", "false").lower() in (
            "1",
            "true",
        )

        try:
            # TODO refactor so we do not specify defaults twice (here and in inveniordm.py)
            records = self.get_inveniordm_requests(self).search_inveniordm_records(
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


class InvenioRDMRecordVariantItemHandler(APIHandler):
    def initialize(self, get_inveniordm_requests: GetInvenioRDMRequests):
        self.get_inveniordm_requests = get_inveniordm_requests

    @tornado.web.authenticated
    def get(self, record_id: str):
        record_identifier = inveniordm_record_identifier(
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
            record = self.get_inveniordm_requests(self).get_inveniordm_record_variant(
                record_identifier
            )
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(record))


class InvenioRDMUserRecordCollectionHandler(APIHandler):
    def initialize(self, get_inveniordm_requests: GetInvenioRDMRequests):
        self.get_inveniordm_requests = get_inveniordm_requests

    @tornado.web.authenticated
    def get(self):
        include_files = self.get_query_argument("include_files", "false").lower() in (
            "1",
            "true",
        )

        try:
            records = self.get_inveniordm_requests(self).list_inveniordm_user_records(
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


class InvenioRDMUserRecordItemHandler(APIHandler):
    def initialize(
        self,
        get_inveniordm_requests: GetInvenioRDMRequests,
        event_bus: EventBus,
    ):
        self.get_inveniordm_requests = get_inveniordm_requests
        self.event_bus = event_bus

    @tornado.web.authenticated
    def delete(self, record_id: str):
        try:
            inveniordm_requests = self.get_inveniordm_requests(self)
            # TODO check if we even need this api call and remove if we dont
            record = inveniordm_requests.get_inveniordm_record_variant(
                InvenioRDMRecordIdentifier(
                    record_id=record_id,
                    record_status="draft",
                )
            )
            parent_id_value = (record.get("parent") or {}).get("id")
            parent_id = str(parent_id_value) if parent_id_value else None
            versions = inveniordm_requests.list_inveniordm_record_versions(
                record_id, include_drafts=True
            )
            inveniordm_requests.delete_inveniordm_record_draft(record_id)
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


class InvenioRDMRecordPermissionHandler(APIHandler):
    def initialize(self, get_inveniordm_requests: GetInvenioRDMRequests):
        self.get_inveniordm_requests = get_inveniordm_requests

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
            inveniordm_requests = self.get_inveniordm_requests(self)
            permission = await asyncio.to_thread(
                inveniordm_requests.get_inveniordm_record_permission,
                record_id,
                cast(InvenioRDMRecordStatus, record_status),
            )  # run this in a thread until we have a proper async implementation of the api calls
        except ValueError as error:
            self.set_status(
                401
                if str(error) == "Missing InvenioRDM request authentication headers"
                else 404
            )
            self.finish(json.dumps({"message": str(error)}))
            return
        except (KeyError, TypeError) as error:
            self.set_status(502)
            self.finish(
                json.dumps({"message": f"Invalid InvenioRDM response: {error}"})
            )
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(permission))


class InvenioRDMRecordVersionCollectionHandler(APIHandler):
    def initialize(
        self,
        get_inveniordm_requests: GetInvenioRDMRequests,
        event_bus: EventBus,
    ):
        self.get_inveniordm_requests = get_inveniordm_requests
        self.event_bus = event_bus

    @tornado.web.authenticated
    async def get(self, record_id: str):
        include_drafts = self.get_query_argument("include_drafts", "true").lower() in (
            "1",
            "true",
        )
        try:
            versions = await asyncio.to_thread(
                self.get_inveniordm_requests(self).list_inveniordm_record_versions,
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
            inveniordm_requests = self.get_inveniordm_requests(self)
            versions = inveniordm_requests.list_inveniordm_record_versions(
                record_id, include_drafts=True
            )
            draft = inveniordm_requests.create_inveniordm_record_version(record_id)
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


class InvenioRDMRecordDraftWithFilesHandler(APIHandler):
    def initialize(
        self,
        get_inveniordm_requests: GetInvenioRDMRequests,
        get_job_manager: GetJobManager,
        event_bus: EventBus,
    ):
        self.get_inveniordm_requests = get_inveniordm_requests
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

        inveniordm_requests = self.get_inveniordm_requests(self)
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

            draft = inveniordm_requests.create_inveniordm_record_draft_with_files(
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


class InvenioRDMRecordFileCollectionHandler(APIHandler):
    def initialize(
        self,
        get_inveniordm_requests: GetInvenioRDMRequests,
        get_job_manager: GetJobManager,
        create_job_metadata: CreateJobMetadata,
        event_bus: EventBus,
    ):
        self.get_inveniordm_requests = get_inveniordm_requests
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

        inveniordm_requests = self.get_inveniordm_requests(self)
        try:
            account_metadata = self.create_job_metadata(inveniordm_requests)
        except ValueError as error:
            self.set_status(401)
            self.finish(json.dumps({"message": str(error)}))
            return
        except KeyError as error:
            self.set_status(502)
            self.finish(
                json.dumps({"message": f"Missing field in InvenioRDM profile: {error}"})
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

            inveniordm_requests.upload_inveniordm_record_files(
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
        file_id = inveniordm_file_identifier(
            data.get("record_id"),
            data.get("record_status"),
            data.get("file_key"),
        )

        if file_id is None or str(file_id.record_id) != record_id:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        try:
            inveniordm_requests = self.get_inveniordm_requests(self)
            inveniordm_requests.delete_inveniordm_record_file(
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
