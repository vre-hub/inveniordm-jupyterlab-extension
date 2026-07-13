from zenodo_jupyterlab.zenodo_requests import zenodo_requests as zenodo_requests_module
from zenodo_jupyterlab.zenodo_requests.zenodo_requests import ZenodoRequests


def test_draft_is_its_own_upload_target(monkeypatch):
    draft = {"id": 12, "submitted": False, "links": {"bucket": "bucket"}}
    monkeypatch.setattr(
        zenodo_requests_module,
        "get_zenodo_deposition",
        lambda *args, **kwargs: draft,
    )

    requests = ZenodoRequests("https://sandbox.zenodo.org", {"Authorization": "x"})

    assert requests.get_zenodo_deposition_upload_target(12) is draft


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

    assert requests.get_zenodo_deposition_upload_target(12) is draft
