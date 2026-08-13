import json

import requests
import tornado

from ..cell_actions import make_inveniordm_import_cell_action
from ..inveniordm_file_identifier import inveniordm_file_identifier
from ..util.sse import EventBus
from .base import (
    APIHandler,
    GetInvenioRDMDownloadManager,
    GetInvenioRDMRequests,
    GetUserSettings,
    _download_status_changed_topic,
    get_user_id,
)


class InvenioRDMFileDownloadHandler(APIHandler):
    def initialize(
        self,
        get_inveniordm_requests: GetInvenioRDMRequests,
        get_inveniordm_download_manager: GetInvenioRDMDownloadManager,
        event_bus: EventBus,
    ):
        self.get_inveniordm_requests = get_inveniordm_requests
        self.get_inveniordm_download_manager = get_inveniordm_download_manager
        self.event_bus = event_bus

    @tornado.web.authenticated
    def post(self):
        data = self.get_json_body() or {}
        record_id = data.get("record_id")
        record_status = data.get("record_status")
        file_key = data.get("file_key")
        file_id = inveniordm_file_identifier(record_id, record_status, file_key)
        if file_id is None:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
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
                self.event_bus.publish(
                    user_id,
                    _download_status_changed_topic(file_id),
                )

        job_id = self.get_inveniordm_download_manager(self).start_download(
            inveniordm_requests,
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
        file_id = inveniordm_file_identifier(record_id, record_status, file_key)
        if file_id is None:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        try:
            result = self.get_inveniordm_download_manager(self).delete_download(
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


class InvenioRDMFileDownloadStatusHandler(APIHandler):
    def initialize(
        self,
        get_inveniordm_requests: GetInvenioRDMRequests,
        get_inveniordm_download_manager: GetInvenioRDMDownloadManager,
    ):
        self.get_inveniordm_requests = get_inveniordm_requests
        self.get_inveniordm_download_manager = get_inveniordm_download_manager

    @tornado.web.authenticated
    def post(self):
        data = self.get_json_body() or {}
        record_id = data.get("record_id")
        record_status = data.get("record_status")
        file_key = data.get("file_key")
        file_id = inveniordm_file_identifier(record_id, record_status, file_key)
        if file_id is None:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        try:
            status = self.get_inveniordm_download_manager(self).get_download_status(
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


class InvenioRDMFileImportCellHandler(APIHandler):
    def initialize(
        self,
        get_inveniordm_requests: GetInvenioRDMRequests,
        get_inveniordm_download_manager: GetInvenioRDMDownloadManager,
    ):
        self.get_inveniordm_requests = get_inveniordm_requests
        self.get_inveniordm_download_manager = get_inveniordm_download_manager

    @tornado.web.authenticated
    def post(self):
        data = self.get_json_body() or {}
        record_id = data.get("record_id")
        record_status = data.get("record_status")
        file_key = data.get("file_key")
        file_id = inveniordm_file_identifier(record_id, record_status, file_key)
        if file_id is None:
            self.set_status(400)
            self.finish(json.dumps({"message": "Invalid file identifier"}))
            return

        try:
            destination = self.get_inveniordm_download_manager(
                self
            ).get_download_location(
                file_id=file_id,
            )
            if not destination.exists():
                raise ValueError("InvenioRDM file has not been downloaded yet")
            action = make_inveniordm_import_cell_action(
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


class InvenioRDMDownloadLocationSettingHandler(APIHandler):
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
