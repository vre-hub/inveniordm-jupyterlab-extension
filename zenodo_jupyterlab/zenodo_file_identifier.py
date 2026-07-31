from dataclasses import dataclass

from .zenodo_record_identifier import (
    ZenodoRecordIdentifier,
    zenodo_record_identifier,
)


@dataclass(frozen=True)
class ZenodoFileIdentifier(ZenodoRecordIdentifier):
    """Identifies one file within a Zenodo record."""

    file_key: str


def zenodo_file_identifier(
    record_id: object,
    record_status: object,
    file_key: object,
) -> ZenodoFileIdentifier | None:
    record_identifier = zenodo_record_identifier(record_id, record_status)
    if record_identifier is None or not isinstance(file_key, str) or not file_key:
        return None
    return ZenodoFileIdentifier(
        record_id=record_identifier.record_id,
        record_status=record_identifier.record_status,
        file_key=file_key,
    )
