from dataclasses import dataclass
from typing import Literal


ZenodoRecordStatus = Literal["draft", "published"]


@dataclass(frozen=True)
class ZenodoFileIdentifier:
    """Identifies one file within a Zenodo record."""

    record_id: int | str
    record_status: ZenodoRecordStatus
    file_key: str


def _zenodo_file_identifier(
    record_id: object,
    record_status: object,
    file_key: object,
) -> ZenodoFileIdentifier | None:
    if (
        not isinstance(record_id, (int, str))
        or isinstance(record_id, bool)
        or record_id == ""
        or record_status not in {"draft", "published"}
        or not isinstance(file_key, str)
        or not file_key
    ):
        return None
    return ZenodoFileIdentifier(
        record_id=record_id,
        record_status=record_status,
        file_key=file_key,
    )
