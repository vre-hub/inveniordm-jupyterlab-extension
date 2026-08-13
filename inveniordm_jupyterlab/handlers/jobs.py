import json

import requests
import tornado

from .base import (
    APIHandler,
    CreateJobMetadata,
    GetInvenioRDMRequests,
    GetJobManager,
)


class JobsHandler(APIHandler):
    """
    Allows clients to list all jobs, optionally filtered by job type and status.
    Can be used to display e.g. download progress after page reload.
    """

    # TODO add SSE to notify clients of new jobs so that client does not have to keep track of the jobs it starts itself
    def initialize(
        self,
        get_job_manager: GetJobManager,
        get_inveniordm_requests: GetInvenioRDMRequests,
        create_job_metadata: CreateJobMetadata,
    ):
        self.get_job_manager = get_job_manager
        self.get_inveniordm_requests = get_inveniordm_requests
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
                    json.dumps(
                        {"message": f"Missing field in InvenioRDM profile: {error}"}
                    )
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
