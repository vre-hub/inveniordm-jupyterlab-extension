from pathlib import Path
from typing import Any, Literal


Framework = Literal["pandas"]


def make_zenodo_import_cell_action(
    *,
    path: Path,
    deposition_id: int | str,
    file_id: str,
    framework: str,
) -> dict[str, Any]:
    if framework != "pandas":
        raise ValueError(f"Unsupported import framework: {framework}")

    path_literal = repr(str(path))
    source = "\n".join(
        [
            "from pathlib import Path",
            "import pandas as pd",
            "",
            f"file_path = Path({path_literal})",
            "df = pd.read_csv(file_path)",
            "df.head()",
        ]
    )

    return {
        "cell_type": "code",
        "source": source,
        "metadata_zenodo_jupyterlab": {
            "kind": "import-cell",
            "version": 1,
            "framework": framework,
            "deposition_id": str(deposition_id),
            "file_id": file_id,
            "path": str(path),
        },
    }
