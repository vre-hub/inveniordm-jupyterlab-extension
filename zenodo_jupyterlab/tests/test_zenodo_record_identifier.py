from zenodo_jupyterlab.zenodo_record_identifier import (
    ZenodoRecordIdentifier,
    zenodo_record_identifier,
)


def test_record_identifier_requires_known_record_status():
    assert zenodo_record_identifier("123", None) is None
    assert zenodo_record_identifier("123", "unknown") is None
    assert zenodo_record_identifier("123", "draft") == ZenodoRecordIdentifier(
        record_id="123",
        record_status="draft",
    )


def test_record_identifier_requires_nonempty_record_id():
    assert zenodo_record_identifier("", "published") is None
    assert zenodo_record_identifier(True, "published") is None
