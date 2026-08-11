from inveniordm_jupyterlab.inveniordm_record_identifier import (
    InvenioRDMRecordIdentifier,
    inveniordm_record_identifier,
)


def test_record_identifier_requires_known_record_status():
    assert inveniordm_record_identifier("123", None) is None
    assert inveniordm_record_identifier("123", "unknown") is None
    assert inveniordm_record_identifier("123", "draft") == InvenioRDMRecordIdentifier(
        record_id="123",
        record_status="draft",
    )


def test_record_identifier_requires_nonempty_record_id():
    assert inveniordm_record_identifier("", "published") is None
    assert inveniordm_record_identifier(True, "published") is None
