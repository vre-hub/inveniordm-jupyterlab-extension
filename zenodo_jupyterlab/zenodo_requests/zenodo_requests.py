from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from ..util.job_types import CancelCheck, JobCancelled, UploadProgressCallback
from ..util.progress_reporting_reader import ProgressReportingReader
from .zenodo import (
    ZenodoFileResponse,
    ZenodoPermission,
    create_zenodo_record_draft,
    create_zenodo_record_version,
    delete_zenodo_draft_file,
    get_zenodo_access_grants,
    get_zenodo_me,
    get_zenodo_record_details,
    get_zenodo_record_file,
    get_zenodo_user_record,
    list_zenodo_record_versions,
    list_zenodo_user_records,
    open_zenodo_file,
    search_zenodo_records,
    upload_zenodo_draft_file,
)
from .zenodo_helpers import include_zenodo_files


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
            include_zenodo_files(
                records.get("hits", {}).get("hits", []),
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
            include_zenodo_files(
                records,
                base_url=self.url,
                headers=self.headers,
            )

        return records

    def list_zenodo_record_versions(
        self,
        record_id: int | str,
    ) -> list[dict[str, Any]]:
        response = list_zenodo_record_versions(
            record_id,
            base_url=self.url,
            headers=self.headers,
        )
        versions = response.get("hits", {}).get("hits", [])

        # Try to find a draft version of the record and include it in the list of versions if it exists
        # (Because drafts are not included in the response of the /api/records/{record_id}/versions endpoint)

        parent_id = next(
            (
                version.get("conceptrecid")
                for version in versions
                if version.get("conceptrecid") is not None
            ),
            None,
        )
        if parent_id is None:
            raise ValueError(
                f"Could not find parent conceptrecid for record {record_id}"
            )

        try:
            family_records = list_zenodo_user_records(
                base_url=self.url,
                headers=self.headers,
                size=25,  # TODO handle if this is too small, instead check if request with ?q=id:parent?id and taking the first result works
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
            if str(record.get("conceptrecid")) == str(parent_id)
            and record.get("status") == "draft"
        ]
        if not drafts:
            return versions

        newest_draft = max(
            drafts,
            key=lambda record: (
                record.get("metadata", {}).get("relations", {}).get("version") or [{}]
            )[0].get("index", -1),
        )
        draft_id = str(newest_draft.get("id"))
        return [
            *[version for version in versions if str(version.get("id")) != draft_id],
            newest_draft,
        ]

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
            include_zenodo_files(
                [user_record],
                base_url=self.url,
                headers=self.headers,
            )
        return user_record

    def get_zenodo_record(
        self,
        record_id: int | str,
    ) -> dict[str, Any]:
        """Return a public Zenodo record, including its embedded files."""
        return get_zenodo_record_details(
            record_id,
            base_url=self.url,
            headers=self.headers,
        )

    def get_zenodo_record_permission(
        self,
        record_id: int | str,
    ) -> ZenodoPermission:
        """Return the authenticated user's effective permission for a record."""
        # Get the record details (either from user records or public record details)
        try:
            record = self.get_zenodo_user_record(record_id, include_files=False)
        except ValueError:
            record = self.get_zenodo_record(record_id)
        except requests.RequestException as error:
            if getattr(error.response, "status_code", None) in (401, 403):
                return "view"
            else:
                raise

        # Get user id
        user_id = self.zenodo_user_id

        # If user is owner, return "manage"
        if any(str(owner.get("id")) == user_id for owner in record.get("owners", [])):
            return "manage"

        # If user is not owner, check access grants
        access_grants_url = record.get("links", {}).get("access_grants")
        if not access_grants_url:
            return "view"

        try:
            grants = get_zenodo_access_grants(
                access_grants_url,
                base_url=self.url,
                headers=self.headers,
            )
        except requests.RequestException as error:
            if getattr(error.response, "status_code", None) == 403:
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

        print(f"Record {record_id} is not published, so its files can be changed")
        return record

    def delete_file_from_record(
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

        self.delete_draft_file(files_url=files_url, file_key=file_key)
        return draft

    def upload_files_to_record(
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

        self.upload_files_to_draft(
            file_paths=file_paths,
            files_url=files_url,
            on_upload_progress=on_upload_progress,
            should_cancel=should_cancel,
        )
        return draft

    def delete_draft_file(
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

    def upload_files_to_draft(
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
                    self.delete_draft_file(
                        files_url=files_url,
                        file_key=path.name,
                    )
                    raise

    def create_minimal_record_draft(
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

        self.upload_files_to_draft(
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
