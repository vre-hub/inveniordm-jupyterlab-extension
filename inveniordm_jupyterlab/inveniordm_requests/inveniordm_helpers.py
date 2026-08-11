from typing import Any

import requests

from .inveniordm import list_inveniordm_record_files


def include_inveniordm_file_if_draft_or_restricted(
    item: dict[str, Any], *, base_url: str, headers: dict[str, str] | None
) -> None:
    """
    Expand a InvenioRDM record in place with its file list if
    - the record is a draft
    - or if the files are restricted.
    Those are the two cases where /api/user/records does not include the files,
    so we need to fetch them separately.
    Search queries to /api/records do not return drafts but the results do not include the files of restricted records,
    therefore we need to call this function on those records also.
    """
    access = item.get("access")
    if item.get("is_draft") or (access and access.get("files") == "restricted"):
        include_inveniordm_file(
            item,
            base_url=base_url,
            headers=headers,
        )


def include_inveniordm_file(
    item: dict[str, Any], *, base_url: str, headers: dict[str, str] | None
) -> None:
    """
    Expand a InvenioRDM record in place with its file list, if InvenioRDM provides a canonical files link.
    """
    files_url = item.get("links", {}).get("files")
    if not files_url:
        return

    try:
        files = list_inveniordm_record_files(
            files_url,
            base_url=base_url,
            headers=headers,
        )
    except requests.HTTPError as error:
        print(f"Failed to fetch files for record {item.get('id')}: {error}")
        return
    entries = files.get("entries")
    # entries is a list, but we want to store it as a dict keyed by the file key for compatibility with the rest of the api
    if isinstance(entries, list):
        files["entries"] = {entry["key"]: entry for entry in entries}
    item["files"] = files
    if item.get("files", dict()).get("count") is None:
        item["files"]["count"] = len(entries) if entries else 0
