from dataclasses import dataclass
from typing import Literal, cast

ZenodoRecordStatus = Literal["draft", "published"]


@dataclass(frozen=True)
class ZenodoRecordIdentifier:
    """Identifies a draft or published representation of a Zenodo record."""

    record_id: int | str
    record_status: ZenodoRecordStatus


def zenodo_record_identifier(
    record_id: object,
    record_status: object,
) -> ZenodoRecordIdentifier | None:
    if (
        not isinstance(record_id, (int, str))
        or isinstance(record_id, bool)
        or record_id == ""
        or record_status not in {"draft", "published"}
    ):
        return None
    return ZenodoRecordIdentifier(
        record_id=record_id,
        record_status=cast(ZenodoRecordStatus, record_status),
    )
