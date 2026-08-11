from dataclasses import dataclass
from typing import Literal, cast

InvenioRDMRecordStatus = Literal["draft", "published"]


@dataclass(frozen=True)
class InvenioRDMRecordIdentifier:
    """Identifies a draft or published representation of a InvenioRDM record."""

    record_id: int | str
    record_status: InvenioRDMRecordStatus


def inveniordm_record_identifier(
    record_id: object,
    record_status: object,
) -> InvenioRDMRecordIdentifier | None:
    if (
        not isinstance(record_id, (int, str))
        or isinstance(record_id, bool)
        or record_id == ""
        or record_status not in {"draft", "published"}
    ):
        return None
    return InvenioRDMRecordIdentifier(
        record_id=record_id,
        record_status=cast(InvenioRDMRecordStatus, record_status),
    )
