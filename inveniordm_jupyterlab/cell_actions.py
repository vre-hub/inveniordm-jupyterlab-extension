import re
from pathlib import Path
from typing import Any

from .inveniordm_file_identifier import InvenioRDMFileIdentifier


def _make_file_variable_name(*, record_id: int | str, path: Path) -> str:
    name = f"{path.stem}_{record_id}"
    name = re.sub(r"\W+", "_", name).strip("_").lower()
    return name or "inveniordm_file"


def _file_comment_name(
    *,
    path: Path,
    file_metadata: dict[str, Any] | None = None,
) -> str:
    if file_metadata is not None:
        filename = (
            file_metadata.get("filename")
            or file_metadata.get("key")
            or file_metadata.get("name")
        )
        if filename:
            safe_filename = Path(str(filename)).name
            if safe_filename:
                return safe_filename

    return path.name


def make_inveniordm_import_cell_action(
    *,
    path: Path,
    file_id: InvenioRDMFileIdentifier,
    file_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path_literal = repr(str(path))
    variable_name = _make_file_variable_name(record_id=file_id.record_id, path=path)
    comment_name = _file_comment_name(path=path, file_metadata=file_metadata)
    source = "\n".join(
        [
            f"# Location of file {comment_name}:",
            f"{variable_name} = {path_literal}",
        ]
    )

    return {
        "cell_type": "code",
        "source": source,
        "metadata_inveniordm_jupyterlab": {
            "kind": "import-cell",
            "version": 1,
            "record_id": str(file_id.record_id),
            "record_status": file_id.record_status,
            "file_key": file_id.file_key,
            "path": str(path),
        },
    }
