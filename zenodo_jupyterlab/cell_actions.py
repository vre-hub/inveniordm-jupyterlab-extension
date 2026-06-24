import re
from pathlib import Path
from typing import Any


def _make_file_variable_name(*, deposition_id: int | str, path: Path) -> str:
    name = f"zenodo_{deposition_id}_{path.stem}"
    name = re.sub(r"\W+", "_", name).strip("_").lower()
    return name or "zenodo_file"


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


def make_zenodo_import_cell_action(
    *,
    path: Path,
    deposition_id: int | str,
    file_id: str,
    file_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path_literal = repr(str(path))
    variable_name = _make_file_variable_name(deposition_id=deposition_id, path=path)
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
        "metadata_zenodo_jupyterlab": {
            "kind": "import-cell",
            "version": 1,
            "deposition_id": str(deposition_id),
            "file_id": file_id,
            "path": str(path),
        },
    }
