from inveniordm_jupyterlab.inveniordm_download_location_manager import (
    InvenioRDMDownloadLocationManager,
)
from inveniordm_jupyterlab.inveniordm_file_identifier import (
    InvenioRDMFileIdentifier,
    inveniordm_file_identifier,
)


def test_draft_and_published_downloads_have_distinct_locations(tmp_path):
    locations = InvenioRDMDownloadLocationManager(tmp_path, "inveniordm_sandbox")
    draft_file = InvenioRDMFileIdentifier(
        record_id="123",
        record_status="draft",
        file_key="data.csv",
    )
    published_file = InvenioRDMFileIdentifier(
        record_id="123",
        record_status="published",
        file_key="data.csv",
    )

    assert locations.download_location(file_id=draft_file) == (
        tmp_path / "inveniordm_sandbox" / "123" / "draft" / "data.csv"
    )
    assert locations.download_location(file_id=published_file) == (
        tmp_path / "inveniordm_sandbox" / "123" / "published" / "data.csv"
    )


def test_file_identifier_requires_known_record_status():
    assert inveniordm_file_identifier("123", None, "data.csv") is None
    assert inveniordm_file_identifier("123", "unknown", "data.csv") is None
    assert inveniordm_file_identifier("123", "draft", "data.csv") == (
        InvenioRDMFileIdentifier(
            record_id="123",
            record_status="draft",
            file_key="data.csv",
        )
    )
