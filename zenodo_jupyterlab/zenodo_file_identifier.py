from dataclasses import dataclass


@dataclass(frozen=True)
class ZenodoFileIdentifier:
    """Identifies one file within a Zenodo record."""

    record_id: int | str
    file_key: str


def _zenodo_file_identifier(
    record_id: object,
    file_key: object,
) -> ZenodoFileIdentifier | None:
    if (
        not isinstance(record_id, (int, str))
        or isinstance(record_id, bool)
        or record_id == ""
        or not isinstance(file_key, str)
        or not file_key
    ):
        return None
    return ZenodoFileIdentifier(record_id=record_id, file_key=file_key)
