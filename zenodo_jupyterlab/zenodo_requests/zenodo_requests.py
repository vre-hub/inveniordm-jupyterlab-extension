from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from zenodo_jupyterlab.zenodo_requests.zenodo_helpers import (
    include_zenodo_file_if_draft_or_restricted,
)

from ..util.job_types import CancelCheck, JobCancelled, UploadProgressCallback
from ..util.progress_reporting_reader import ProgressReportingReader
from .zenodo import (
    ZenodoFileResponse,
    ZenodoPermission,
    check_user_record_permission_workaround,
    create_zenodo_record_draft,
    create_zenodo_record_version,
    delete_zenodo_draft_file,
    get_zenodo_me,
    get_zenodo_record,
    get_zenodo_record_file,
    get_zenodo_user_record,
    list_zenodo_access_grants,
    list_zenodo_record_versions,
    list_zenodo_user_records,
    open_zenodo_file,
    search_zenodo_records,
    upload_zenodo_draft_file,
)


@dataclass
class AccessTokenStatus:
    access_token_present: bool
    access_token_valid: bool
    sandbox: bool


class ZenodoRequests:
    """
    Wrapper around Zenodo API requests for a specific user/token,
    using caller-provided headers for authentication.
    """

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        zenodo_user_id: str | None = None,
    ):
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.zenodo_user_id = zenodo_user_id

    def get_zenodo_me(self) -> dict[str, Any]:
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        return get_zenodo_me(
            base_url=self.url,
            headers=self.headers,
        )

    def search_zenodo_records(
        self,
        *,
        query: str,
        page: int = 1,
        size: int = 10,
        sort: str = "bestmatch",
        allversions: bool = False,
        include_files: bool = False,
    ) -> dict[str, Any]:
        records = search_zenodo_records(
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
                include_zenodo_file_if_draft_or_restricted(
                    record,
                    base_url=self.url,
                    headers=self.headers,
                )

        return records

    def list_zenodo_user_records(
        self,
        *,
        page: int = 1,
        size: int = 10,
        include_files: bool = False,
    ) -> list[dict[str, Any]]:
        records = list_zenodo_user_records(
            base_url=self.url,
            headers=self.headers,
            page=page,
            size=size,
        )
        if include_files:
            for record in records:
                include_zenodo_file_if_draft_or_restricted(
                    record,
                    base_url=self.url,
                    headers=self.headers,
                )

        return records

    def list_zenodo_record_versions(
        self,
        record_id: int | str,
        include_drafts: bool = True,
    ) -> list[dict[str, Any]]:
        response = list_zenodo_record_versions(
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
                    get_zenodo_user_record(
                        record_id,
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
            family_records = list_zenodo_user_records(
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
            for record in family_records
            if str(record.get("parent", {}).get("id")) == str(parent_id)
            and record.get("is_draft", False) is True
        ]
        if not drafts:
            return versions

        # New version drafts are not included in the public versions endpoint,
        # so we need to query the user records endpoint to find it if it exists.
        # Also, drafts may represent published versions that are being edited, in
        # which case the public versions endpoint already returned a record with the same ID,
        # but we want to return the draft because we assume the user is interested in editing it.
        # Therefore, add every draft after the published versions
        # so that it replaces the published representation during deduplication (if present).
        versions_by_id = {
            str(version.get("id")): version for version in [*versions, *drafts]
        }
        return list(versions_by_id.values())

    def get_zenodo_user_record(
        self,
        record_id: int | str,
        *,
        include_files: bool = True,
    ) -> dict[str, Any]:
        """Return a user record, optionally expanding its linked files."""
        user_record = get_zenodo_user_record(
            record_id,
            base_url=self.url,
            headers=self.headers,
        )

        if include_files:
            # For user records that are drafts, the files are not included here,
            # so fetch them separately when the caller needs them.
            include_zenodo_file_if_draft_or_restricted(
                user_record,
                base_url=self.url,
                headers=self.headers,
            )
        return user_record

    def get_zenodo_record(
        self,
        record_id: int | str,
    ) -> dict[str, Any]:
        """Return a public Zenodo record, optionally expanding its linked files."""
        record = get_zenodo_record(
            record_id,
            base_url=self.url,
            headers=self.headers,
        )
        return record

    def get_zenodo_record_permission(
        self,
        record_id: int | str,
    ) -> ZenodoPermission:
        """Return the authenticated user's effective permission for a user record."""
        # Get user id
        user_id = self.zenodo_user_id
        if user_id is None:
            raise ValueError(
                "Zenodo user ID is not set for this ZenodoRequests instance"
            )

        # Get the record details
        record = self.get_zenodo_user_record(record_id, include_files=False)

        # If user is owner, return "manage"
        owner_id = (
            record.get("parent", {}).get("access", {}).get("owned_by", {}).get("user")
        )
        if str(owner_id) == user_id:
            return "manage"

        # If user is not owner, check access grants
        access_grants_url = record.get("links", {}).get("access_grants")
        if not access_grants_url:
            raise ValueError("Record does not provide an access grants link")

        try:
            grants = list_zenodo_access_grants(
                access_grants_url,
                base_url=self.url,
                headers=self.headers,
            )
        except requests.RequestException as error:
            if getattr(error.response, "status_code", None) == 403:
                has_edit = check_user_record_permission_workaround(
                    record_id=record_id,
                    user_id=user_id,
                    permission_to_check="edit",
                    base_url=self.url,
                    headers=self.headers,
                )
                if has_edit:
                    return "edit"
                return "view"
            raise

        permissions: list[ZenodoPermission] = []
        for grant in grants.get("hits", {}).get("hits", []):
            subject = grant.get("subject", {})
            permission = grant.get("permission")
            if (
                subject.get("type") == "user"
                and str(subject.get("id")) == user_id
                and permission in {"manage", "edit", "preview", "view"}
            ):
                permissions.append(permission)

        # select the highest permission the user has, defaulting to "view" if none found
        permission_order: tuple[ZenodoPermission, ...] = (
            "manage",
            "edit",
            "preview",
            "view",
        )
        perm = next(
            (
                permission
                for permission in permission_order
                if permission in permissions
            ),
            "view",
        )
        if perm not in permission_order:
            raise ValueError(f"Unexpected permission value: {perm}")
        return perm

    def create_zenodo_record_version(
        self,
        record_id: int | str,
    ) -> dict[str, Any]:
        """Create an editable new-version draft for a published record."""
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        return create_zenodo_record_version(
            record_id,
            base_url=self.url,
            headers=self.headers,
        )

    def _get_editable_record_draft(
        self,
        record_id: int | str,
    ) -> dict[str, Any]:
        """
        Return the editable draft used to change a record's files.

        Published records are immutable and must be explicitly versioned
        before their files can be changed.
        """
        record = self.get_zenodo_user_record(record_id, include_files=False)
        if record.get("is_published"):
            raise ValueError(
                f"Record {record_id} is published and cannot be edited as a draft"
            )

        return record

    def delete_zenodo_record_file(
        self,
        *,
        record_id: int | str,
        file_key: str,
    ) -> dict[str, Any]:
        """Delete a file from the editable draft of a record."""
        draft = self._get_editable_record_draft(record_id)
        files_url = draft.get("links", {}).get("files")
        if not files_url:
            raise ValueError("Record draft does not provide a files link")

        self.delete_zenodo_draft_file(files_url=files_url, file_key=file_key)
        return draft

    def upload_zenodo_record_files(
        self,
        *,
        record_id: int | str,
        file_paths: list[Path],
        on_upload_progress: UploadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> dict[str, Any]:
        """Upload files to the editable draft of a record."""
        draft = self._get_editable_record_draft(record_id)
        files_url = draft.get("links", {}).get("files")
        if not files_url:
            raise ValueError("Record draft does not provide a files link")

        self.upload_zenodo_draft_files(
            file_paths=file_paths,
            files_url=files_url,
            on_upload_progress=on_upload_progress,
            should_cancel=should_cancel,
        )
        return draft

    def delete_zenodo_draft_file(
        self,
        *,
        files_url: str,
        file_key: str,
    ) -> None:
        """
        Delete a file from an InvenioRDM draft's file collection.
        """
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        delete_zenodo_draft_file(
            files_url,
            base_url=self.url,
            headers=self.headers,
            file_key=file_key,
        )

    def upload_zenodo_draft_files(
        self,
        file_paths: list[Path],
        files_url: str,
        on_upload_progress: UploadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ):
        """
        Upload files on the local filesystem to an InvenioRDM draft.
        """
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

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
                    nonlocal bytes_uploaded
                    bytes_uploaded += chunk_size
                    if on_upload_progress is not None:
                        on_upload_progress(
                            bytes_uploaded,
                            total_bytes,
                            current_file,
                        )

                try:
                    upload_zenodo_draft_file(
                        files_url,
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
                    self.delete_zenodo_draft_file(
                        files_url=files_url,
                        file_key=path.name,
                    )
                    raise

    def create_zenodo_record_draft_with_files(
        self,
        *,
        file_paths: list[Path],
        on_upload_progress: UploadProgressCallback | None = None,
        should_cancel: CancelCheck | None = None,
    ) -> dict[str, Any]:
        if not self.headers:
            raise ValueError("Missing Zenodo request authentication headers")

        if should_cancel is not None and should_cancel():
            raise JobCancelled("Upload canceled")

        draft = create_zenodo_record_draft(
            base_url=self.url,
            headers=self.headers,
        )
        if should_cancel is not None and should_cancel():
            raise JobCancelled("Upload canceled")
        files_url = draft["links"]["files"]

        self.upload_zenodo_draft_files(
            file_paths=file_paths,
            files_url=files_url,
            on_upload_progress=on_upload_progress,
            should_cancel=should_cancel,
        )
        return draft

    def open_zenodo_file(
        self,
        *,
        file_url: str,
    ) -> ZenodoFileResponse:
        return open_zenodo_file(
            file_url,
            base_url=self.url,
            headers=self.headers,
        )

    def get_zenodo_record_file(
        self,
        *,
        record_id: int | str,
        file_key: str,
    ) -> dict[str, Any]:
        return get_zenodo_record_file(
            record_id,
            file_key,
            base_url=self.url,
            headers=self.headers,
        )
