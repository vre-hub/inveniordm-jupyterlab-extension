import re
from pathlib import Path
from typing import Any


def _make_file_variable_name(*, deposition_id: int | str, path: Path) -> str:
    name = f"zenodo_{deposition_id}_{path.stem}"
    name = re.sub(r"\W+", "_", name).strip("_").lower()
    return name or "zenodo_file"


def make_zenodo_import_cell_action(
    *,
    path: Path,
    deposition_id: int | str,
    file_id: str,
) -> dict[str, Any]:
    path_literal = repr(str(path))
    variable_name = _make_file_variable_name(deposition_id=deposition_id, path=path)
    source = "\n".join(
        [
            f"# Location of file {path.name}:",
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
