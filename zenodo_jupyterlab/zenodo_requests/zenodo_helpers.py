from typing import Any

from .zenodo import list_zenodo_record_files


def include_zenodo_files(
    items: list[dict[str, Any]],
    *,
    base_url: str,
    headers: dict[str, str] | None,
) -> None:
    """
    Expand Zenodo resources in place with their file list, if Zenodo provides
    a canonical files link.
    """
    for item in items:
        files_url = item.get("links", {}).get("files")
        if not files_url:
            continue

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
