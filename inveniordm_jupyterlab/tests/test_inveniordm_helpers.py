import pytest

from inveniordm_jupyterlab.inveniordm_requests import inveniordm_helpers


def test_include_inveniordm_file_returns_entries_as_map(monkeypatch):
    item = {
        "id": "record-1",
        "links": {"files": "https://inveniordm.org/api/records/record-1/files"},
    }
    files = {
        "entries": [
            {"key": "data.csv", "size": 10},
            {"key": "analysis.ipynb", "size": 20},
        ]
    }
    monkeypatch.setattr(
        inveniordm_helpers,
        "list_inveniordm_record_files",
        lambda *args, **kwargs: files,
    )

    inveniordm_helpers.include_inveniordm_file(
        item,
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )

    assert item["files"]["entries"] == {
        "data.csv": {"key": "data.csv", "size": 10},
        "analysis.ipynb": {"key": "analysis.ipynb", "size": 20},
    }


def test_include_inveniordm_file_without_files_link_does_nothing(monkeypatch):
    item = {"id": "record-1", "links": {}}
    monkeypatch.setattr(
        inveniordm_helpers,
        "list_inveniordm_record_files",
        lambda *args, **kwargs: pytest.fail("files should not be fetched"),
    )

    inveniordm_helpers.include_inveniordm_file(
        item,
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )

    assert "files" not in item


@pytest.mark.parametrize(
    "record",
    [
        {"is_draft": True},
        {"is_draft": False, "access": {"files": "restricted"}},
    ],
)
def test_include_inveniordm_file_if_draft_or_restricted_includes_files(
    monkeypatch, record
):
    calls = []
    monkeypatch.setattr(
        inveniordm_helpers,
        "include_inveniordm_file",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    inveniordm_helpers.include_inveniordm_file_if_draft_or_restricted(
        record,
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )

    assert calls == [
        (
            (record,),
            {
                "base_url": "https://inveniordm.org",
                "headers": {"Authorization": "x"},
            },
        )
    ]


@pytest.mark.parametrize(
    "record",
    [
        {},
        {"is_draft": False},
        {"is_draft": False, "access": {"files": "public"}},
    ],
)
def test_include_inveniordm_file_if_draft_or_restricted_skips_public_records(
    monkeypatch, record
):
    monkeypatch.setattr(
        inveniordm_helpers,
        "include_inveniordm_file",
        lambda *args, **kwargs: pytest.fail("files should not be fetched"),
    )

    inveniordm_helpers.include_inveniordm_file_if_draft_or_restricted(
        record,
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )
