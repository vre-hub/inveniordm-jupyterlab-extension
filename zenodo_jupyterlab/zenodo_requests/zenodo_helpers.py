from typing import Any

from .zenodo import list_zenodo_record_files


def include_zenodo_file_if_draft_or_restricted(
    item: dict[str, Any], *, base_url: str, headers: dict[str, str] | None
) -> None:
    """
    Expand a Zenodo record in place with its file list if
    - the record is a draft
    - or if the files are restricted.
    Those are the two cases where /api/user/records does not include the files,
    so we need to fetch them separately.
    It should not be necessary to call this on results of /api/records,
    since that endpoint should always include the files.
    """
    access = item.get("access")
    if item.get("is_draft") or (access and access.get("files") == "restricted"):
        include_zenodo_file(
            item,
            base_url=base_url,
            headers=headers,
        )


def include_zenodo_file(
    item: dict[str, Any], *, base_url: str, headers: dict[str, str] | None
) -> None:
    """
    Expand a Zenodo record in place with its file list, if Zenodo provides a canonical files link.
    """
    files_url = item.get("links", {}).get("files")
    if not files_url:
        return

    files = list_zenodo_record_files(
        files_url,
        base_url=base_url,
        headers=headers,
    )
    entries = files.get("entries")
    # entries is a list, but we want to store it as a dict keyed by the file key for compatibility with the rest of the api
    if isinstance(entries, list):
        files["entries"] = {entry["key"]: entry for entry in entries}
    item["files"] = files
