from dataclasses import dataclass

from .inveniordm_record_identifier import (
    InvenioRDMRecordIdentifier,
    inveniordm_record_identifier,
)


@dataclass(frozen=True)
class InvenioRDMFileIdentifier(InvenioRDMRecordIdentifier):
    """Identifies one file within a InvenioRDM record."""

    file_key: str


def inveniordm_file_identifier(
    record_id: object,
    record_status: object,
    file_key: object,
) -> InvenioRDMFileIdentifier | None:
    record_identifier = inveniordm_record_identifier(record_id, record_status)
    if record_identifier is None or not isinstance(file_key, str) or not file_key:
        return None
    return InvenioRDMFileIdentifier(
        record_id=record_identifier.record_id,
        record_status=record_identifier.record_status,
        file_key=file_key,
    )
