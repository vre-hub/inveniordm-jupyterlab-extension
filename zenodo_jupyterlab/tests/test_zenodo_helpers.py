from zenodo_jupyterlab.zenodo_requests import zenodo_helpers


def test_include_zenodo_files_returns_entries_as_map(monkeypatch):
    items = [
        {
            "id": "record-1",
            "links": {"files": "https://zenodo.org/api/records/record-1/files"},
        }
    ]
    files = {
        "entries": [
            {"key": "data.csv", "size": 10},
            {"key": "analysis.ipynb", "size": 20},
        ]
    }
    monkeypatch.setattr(
        zenodo_helpers,
        "list_zenodo_record_files",
        lambda *args, **kwargs: files,
    )

    zenodo_helpers.include_zenodo_files(
        items,
        base_url="https://zenodo.org",
        headers={"Authorization": "x"},
    )

    assert items[0]["files"]["entries"] == {
        "data.csv": {"key": "data.csv", "size": 10},
        "analysis.ipynb": {"key": "analysis.ipynb", "size": 20},
    }
