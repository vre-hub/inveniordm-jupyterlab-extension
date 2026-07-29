from zenodo_jupyterlab.zenodo_download_location_manager import (
    ZenodoDownloadLocationManager,
)
from zenodo_jupyterlab.zenodo_file_identifier import (
    ZenodoFileIdentifier,
    _zenodo_file_identifier,
)


def test_draft_and_published_downloads_have_distinct_locations(tmp_path):
    locations = ZenodoDownloadLocationManager(tmp_path)
    draft_file = ZenodoFileIdentifier(
        record_id="123",
        record_status="draft",
        file_key="data.csv",
    )
    published_file = ZenodoFileIdentifier(
        record_id="123",
        record_status="published",
        file_key="data.csv",
    )

    assert locations.download_location(file_id=draft_file) == (
        tmp_path / "123" / "draft" / "data.csv"
    )
    assert locations.download_location(file_id=published_file) == (
        tmp_path / "123" / "published" / "data.csv"
    )


def test_file_identifier_requires_known_record_status():
    assert _zenodo_file_identifier("123", None, "data.csv") is None
    assert _zenodo_file_identifier("123", "unknown", "data.csv") is None
    assert _zenodo_file_identifier("123", "draft", "data.csv") == (
        ZenodoFileIdentifier(
            record_id="123",
            record_status="draft",
            file_key="data.csv",
        )
    )
