from typing import Any

from .zenodo import get_zenodo_files


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

        item["files"] = get_zenodo_files(
            files_url,
            base_url=base_url,
            headers=headers,
        )
