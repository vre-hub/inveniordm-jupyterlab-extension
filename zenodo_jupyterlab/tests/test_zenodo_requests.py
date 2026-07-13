from zenodo_jupyterlab.zenodo_requests import zenodo as zenodo_module
from zenodo_jupyterlab.zenodo_requests import zenodo_requests as zenodo_requests_module
from zenodo_jupyterlab.zenodo_requests.zenodo_requests import ZenodoRequests


def test_draft_is_its_own_file_edit_target(monkeypatch):
    draft = {"id": 12, "submitted": False, "links": {"bucket": "bucket"}}
    monkeypatch.setattr(
        zenodo_requests_module,
        "get_zenodo_deposition",
        lambda *args, **kwargs: draft,
    )

    requests = ZenodoRequests("https://sandbox.zenodo.org", {"Authorization": "x"})

    assert requests.get_zenodo_deposition_file_edit_target(12) is draft


def test_published_deposition_uses_latest_version_draft(monkeypatch):
    published = {"id": 12, "submitted": True}
    version = {
        "links": {
            "latest_draft": "https://sandbox.zenodo.org/api/deposit/depositions/13"
        }
    }
    draft = {"id": 13, "submitted": False, "links": {"bucket": "bucket"}}
    monkeypatch.setattr(
        zenodo_requests_module,
        "get_zenodo_deposition",
        lambda *args, **kwargs: published,
    )
    monkeypatch.setattr(
        zenodo_requests_module,
        "create_zenodo_deposition_version",
        lambda *args, **kwargs: version,
    )
    monkeypatch.setattr(
        zenodo_requests_module,
        "get_zenodo_deposition_at_url",
        lambda *args, **kwargs: draft,
    )

    requests = ZenodoRequests("https://sandbox.zenodo.org", {"Authorization": "x"})

    assert requests.get_zenodo_deposition_file_edit_target(12) is draft


def test_delete_file_from_bucket(monkeypatch):
    calls = []
    monkeypatch.setattr(
        zenodo_requests_module,
        "delete_zenodo_deposition_file",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    requests = ZenodoRequests("https://sandbox.zenodo.org", {"Authorization": "x"})
    requests.delete_file_from_bucket(
        bucket_url="https://sandbox.zenodo.org/api/files/bucket",
        file_key="data.csv",
    )

    assert calls == [
        (
            ("https://sandbox.zenodo.org/api/files/bucket",),
            {
                "base_url": "https://sandbox.zenodo.org",
                "headers": {"Authorization": "x"},
                "file_key": "data.csv",
            },
        )
    ]


def test_delete_zenodo_deposition_file_uses_bucket_key(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

    calls = []
    monkeypatch.setattr(
        zenodo_module.requests,
        "delete",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(),
    )

    zenodo_module.delete_zenodo_deposition_file(
        "https://zenodo.org/api/files/bucket-id",
        base_url="https://sandbox.zenodo.org",
        headers={"Authorization": "x"},
        file_key="results 2026.csv",
    )

    assert calls == [
        (
            (
                "https://sandbox.zenodo.org/api/files/"
                "bucket-id/results%202026.csv",
            ),
            {
                "headers": {
                    "Accept": "application/json",
                    "Authorization": "x",
                },
                "timeout": 10,
            },
        )
    ]
