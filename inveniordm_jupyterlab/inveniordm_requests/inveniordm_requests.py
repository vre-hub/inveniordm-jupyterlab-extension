from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from inveniordm_auth.remote_servers import RemoteServerId
from inveniordm_jupyterlab.inveniordm_requests.inveniordm_helpers import (
    include_inveniordm_file_if_draft_or_restricted,
)

from ..inveniordm_file_identifier import InvenioRDMFileIdentifier
from ..inveniordm_record_identifier import (
    InvenioRDMRecordIdentifier,
    InvenioRDMRecordStatus,
)
from ..util.job_types import CancelCheck, JobCancelled, UploadProgressCallback
from ..util.progress_reporting_reader import ProgressReportingReader
from .inveniordm import (
    InvenioRDMFileResponse,
    InvenioRDMPermission,
    InvenioRDMRecordSearchResponse,
    check_user_record_permission_workaround,
    create_inveniordm_record_draft,
    create_inveniordm_record_version,
    delete_inveniordm_draft_file,
    delete_inveniordm_record_draft,
    get_inveniordm_me,
    get_inveniordm_record_public_or_draft,
    list_inveniordm_record_versions,
    list_inveniordm_user_records,
    open_inveniordm_file,
    search_inveniordm_records,
    upload_inveniordm_draft_file,
)


@dataclass
class AccessTokenStatus:
    """Summarize authentication state for a configured remote server."""

    access_token_present: bool
    access_token_valid: bool
    remote_server_id: RemoteServerId
    remote_server_label: str
    remote_server_base_url: str


class InvenioRDMRequests:
    """
    Wrapper around InvenioRDM API requests for a specific user/token,
    using caller-provided headers for authentication.
    """

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        inveniordm_user_id: str | None = None,
    ):
        """Initialize a server-scoped client with optional authentication."""
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.inveniordm_user_id = inveniordm_user_id

    def get_inveniordm_me(self) -> dict[str, Any]:
        """Return the authenticated InvenioRDM user's profile."""
        if not self.headers:
            raise ValueError("Missing InvenioRDM request authentication headers")

        return get_inveniordm_me(
            base_url=self.url,
            headers=self.headers,
        )

    def search_inveniordm_records(
        self,
        *,
        query: str,
        page: int = 1,
        size: int = 10,
        sort: str = "bestmatch",
        allversions: bool = False,
        include_files: bool = False,
    ) -> InvenioRDMRecordSearchResponse:
        """Search records and optionally hydrate protected file metadata."""
        records = search_inveniordm_records(
            query,
            base_url=self.url,
            headers=self.headers,
            page=page,
            size=size,
            sort=sort,
            allversions=allversions,
        )
        if include_files:
            for record in records.get("hits", {}).get("hits", []):
                include_inveniordm_file_if_draft_or_restricted(
                    record,
                    base_url=self.url,
                    headers=self.headers,
                )

        return records

    def list_inveniordm_user_records(
        self,
        *,
        page: int = 1,
        size: int = 10,
        include_files: bool = False,
    ) -> InvenioRDMRecordSearchResponse:
        """List the user's records and optionally hydrate file metadata."""
        records = list_inveniordm_user_records(
            base_url=self.url,
            headers=self.headers,
            page=page,
            size=size,
        )
        if include_files:
            for record in records.get("hits", {}).get("hits", []):
                include_inveniordm_file_if_draft_or_restricted(
                    record,
                    base_url=self.url,
                    headers=self.headers,
                )

        return records

    def list_inveniordm_record_versions(
        self,
        record_id: int | str,
        include_drafts: bool = True,
    ) -> list[dict[str, Any]]:
        """List published versions and, when accessible, editable drafts.

        InvenioRDM's versions endpoint omits drafts. This method supplements its
        results by resolving an initial draft directly or by finding drafts with
        the same parent record, while preserving published and draft variants that
        happen to share a record ID.
        """
        response = list_inveniordm_record_versions(
            record_id,
            base_url=self.url,
            headers=self.headers,
        )
        versions = response.get("hits", {}).get("hits", [])

        if not include_drafts:
            return versions

        # The public versions endpoint only contains published records. For an
        # initial draft there are no published versions from which to derive
        # the parent ID, so resolve that draft directly.
        if not versions:
            try:
                return [
                    get_inveniordm_record_public_or_draft(
                        record_id,
                        record_status="draft",
                        base_url=self.url,
                        headers=self.headers,
                    )
                ]
            except requests.HTTPError as error:
                status_code = getattr(error.response, "status_code", None)
                if status_code not in (401, 403, 404):
                    raise
                return []

        # Try to find a new version draft of the record and include it in the list of versions if it exists
        # (Because drafts are not included in the response of the /api/records/{record_id}/versions endpoint)
        # Strategy: find the parent ID of the record, then list all user records and find the newest draft with that parent ID

        # TODO we only need to do that if there is something newer than the latest published version
        # I thought we could change this to only atttempt to find the new version draft if record.versions.is_latest_draft is false
        # because that is false for the latest draft or published version also.
        # The problem with that is if we have a draft that is not the latest draft (e.g. of a published version)
        # then we would not find it and the dropdown could not show that this record is a draft.

        parent_id = next(
            (
                version.get("parent", {}).get("id")
                for version in versions
                if version.get("parent", {}).get("id") is not None
            ),
            None,
        )
        if parent_id is None:
            raise ValueError(f"Could not find parent ID for record {record_id}")

        try:
            family_records = list_inveniordm_user_records(
                base_url=self.url,
                headers=self.headers,
                query=f"parent.id:{parent_id}",
                size=25,  # TODO handle if this is too small
                allversions=True,
            )
        except requests.HTTPError as error:
            status_code = getattr(error.response, "status_code", None)
            if status_code not in (401, 403):
                raise
            # User records are only needed to supplement the public versions
            # with an editable draft. Callers without that permission can still
            # see the versions returned by the public records endpoint.
            return versions
        drafts = [
            record
            for record in family_records.get("hits", {}).get("hits", [])
            if str(record.get("parent", {}).get("id")) == str(parent_id)
            and record.get("is_draft", False) is True
        ]
        if not drafts:
            return versions

        # Drafts and published records are distinct representations even when
        # they have the same record ID, so preserve both in the version list.
        return [*versions, *drafts]

    def get_inveniordm_record_variant(
        self,
        record_identifier: InvenioRDMRecordIdentifier,
    ) -> dict[str, Any]:
        """Return the requested draft or published InvenioRDM record."""
        record = get_inveniordm_record_public_or_draft(
            record_identifier.record_id,
            record_status=record_identifier.record_status,
            base_url=self.url,
            headers=self.headers,
        )
        return record

    def get_inveniordm_record_permission(
        self,
        record_id: int | str,
        record_status: InvenioRDMRecordStatus,
    ) -> InvenioRDMPermission:
        """
        Return the authenticated user's effective permission for a record.

        This is just a workaround because the InvenioRDM API does not include permissions in the record metadata.
        Remove this if https://github.com/inveniosoftware/invenio-app-rdm/issues/3551 is ever implemented.
        """
        # Get user id
        user_id = self.inveniordm_user_id
        if user_id is None:
            raise ValueError(
                "InvenioRDM user ID is not set. Cannot determine record permission."
            )

        # Fetch the requested variant directly.
        record = get_inveniordm_record_public_or_draft(
            record_id,
            record_status=record_status,
            base_url=self.url,
            headers=self.headers,
        )

        # if record.parent.access.grants exists, return "manage"
        # this is the case if we are the owner of the record or have been granted manage access
        if record.get("parent", {}).get("access", {}).get("grants") is not None:
            return "manage"

        # the only options that are left are "edit" and "preview"
        has_edit = check_user_record_permission_workaround(
            record_id=record_id,
            user_id=user_id,
            permission_to_check="edit",
            base_url=self.url,
            headers=self.headers,
        )
        if has_edit:
            return "edit"
        return "preview"

    def create_inveniordm_record_version(
        self,
        record_id: int | str,
    ) -> dict[str, Any]:
        """Create an editable new-version draft for a published record."""
        if not self.headers:
            raise ValueError("Missing InvenioRDM request authentication headers")

        return create_inveniordm_record_version(
            record_id,
            base_url=self.url,
            headers=self.headers,
        )

    def delete_inveniordm_record_file(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> None:
        """Delete a file from the editable draft of a record."""
        if not self.headers:
            raise ValueError("Missing InvenioRDM request authentication headers")

        delete_inveniordm_draft_file(
            file_id.record_id,
            base_url=self.url,
            headers=self.headers,
            file_key=file_id.file_key,
        )

    def delete_inveniordm_record_draft(self, record_id: int | str) -> None:
        """Discard an editable record draft."""
        if not self.headers:
            raise ValueError("Missing InvenioRDM request authentication headers")

        delete_inveniordm_record_draft(
            record_id,
            base_url=self.url,
            headers=self.headers,
        )

    def upload_inveniordm_record_files(
        self,
        *,
        record_id: int | str,
        file_paths: list[Path],
        on_upload_progress: UploadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> None:
        """Upload files to the editable draft of a record."""
        if not self.headers:
            raise ValueError("Missing InvenioRDM request authentication headers")

        filenames = [path.name for path in file_paths]
        if len(filenames) != len(set(filenames)):
            raise ValueError("Selected files must have unique filenames")

        total_bytes = sum(path.stat().st_size for path in file_paths)
        bytes_uploaded = 0
        if on_upload_progress is not None:
            on_upload_progress(bytes_uploaded, total_bytes, None)

        for path in file_paths:
            if should_cancel is not None and should_cancel():
                raise JobCancelled("Upload canceled")
            with path.open("rb") as file:

                def on_bytes_read(
                    chunk_size: int,
                    *,
                    current_file: str = path.name,
                ) -> None:
                    """Accumulate bytes read and report aggregate upload progress."""
                    nonlocal bytes_uploaded
                    bytes_uploaded += chunk_size
                    if on_upload_progress is not None:
                        on_upload_progress(
                            bytes_uploaded,
                            total_bytes,
                            current_file,
                        )

                try:
                    upload_inveniordm_draft_file(
                        record_id,
                        base_url=self.url,
                        headers=self.headers,
                        filename=path.name,
                        content=ProgressReportingReader(
                            file,
                            on_bytes_read=on_bytes_read,
                            should_cancel=should_cancel,
                        ),
                    )
                except JobCancelled:
                    # Initializing an InvenioRDM upload creates the file entry
                    # before the content is streamed. Remove that empty entry
                    # when streaming is canceled.
                    self.delete_inveniordm_record_file(
                        file_id=InvenioRDMFileIdentifier(
                            record_id=record_id,
                            record_status="draft",
                            file_key=path.name,
                        )
                    )
                    raise

    def create_inveniordm_record_draft_with_files(
        self,
        *,
        file_paths: list[Path],
        on_upload_progress: UploadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> dict[str, Any]:
        """Create a draft and upload files with cooperative cancellation.

        Cancellation is checked both before and after draft creation to avoid
        starting file transfers once the caller has requested a stop.
        """
        if not self.headers:
            raise ValueError("Missing InvenioRDM request authentication headers")

        if should_cancel is not None and should_cancel():
            raise JobCancelled("Upload canceled")

        draft = create_inveniordm_record_draft(
            base_url=self.url,
            headers=self.headers,
        )
        if should_cancel is not None and should_cancel():
            raise JobCancelled("Upload canceled")
        self.upload_inveniordm_record_files(
            file_paths=file_paths,
            record_id=draft["id"],
            on_upload_progress=on_upload_progress,
            should_cancel=should_cancel,
        )
        return draft

    def open_inveniordm_file(
        self,
        *,
        file_id: InvenioRDMFileIdentifier,
    ) -> InvenioRDMFileResponse:
        """Open a streaming response for a draft or published record file."""
        return open_inveniordm_file(
            file_id,
            base_url=self.url,
            headers=self.headers,
        )
