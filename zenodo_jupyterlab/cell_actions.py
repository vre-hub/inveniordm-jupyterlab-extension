from pathlib import Path
from typing import Any, Literal



def make_zenodo_import_cell_action(
    *,
    path: Path,
    deposition_id: int | str,
    file_id: str,
) -> dict[str, Any]:
    path_literal = repr(str(path))
    source = "\n".join(
        [
            f"# Location of file {path.name}:",
            f"file_path = {path_literal}",
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
