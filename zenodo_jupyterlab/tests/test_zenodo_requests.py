import pytest

from zenodo_jupyterlab.zenodo_requests import zenodo as zenodo_module
from zenodo_jupyterlab.zenodo_requests import zenodo_requests as zenodo_requests_module
from zenodo_jupyterlab.zenodo_requests.zenodo_requests import ZenodoRequests
from zenodo_jupyterlab.util.job_types import JobCancelled


class Response:
    def __init__(self, data=None, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"Unexpected HTTP status {self.status_code}")


def test_draft_is_its_own_file_edit_target(monkeypatch):
    draft = {
        "id": "draft-1",
        "is_published": False,
        "links": {"files": "/api/records/draft-1/draft/files"},
    }
    monkeypatch.setattr(
        zenodo_requests_module,
        "get_zenodo_record",
        lambda *args, **kwargs: draft,
    )

    requests = ZenodoRequests("https://sandbox.zenodo.org", {"Authorization": "x"})

    assert requests._get_editable_record_draft("draft-1") is draft


def test_published_record_creates_new_version(monkeypatch):
    published = {"id": "record-1", "is_published": True}
    draft = {
        "id": "draft-2",
        "is_published": False,
        "links": {"files": "/api/records/draft-2/draft/files"},
    }
    monkeypatch.setattr(
        zenodo_requests_module,
        "get_zenodo_record",
        lambda *args, **kwargs: published,
    )
    monkeypatch.setattr(
        zenodo_requests_module,
        "create_zenodo_record_version",
        lambda *args, **kwargs: draft,
    )

    requests = ZenodoRequests("https://sandbox.zenodo.org", {"Authorization": "x"})

    assert requests._get_editable_record_draft("record-1") is draft


def test_create_record_version_uses_authenticated_request(monkeypatch):
    draft = {"id": "draft-2", "is_published": False}
    calls = []
    monkeypatch.setattr(
        zenodo_requests_module,
        "create_zenodo_record_version",
        lambda *args, **kwargs: calls.append((args, kwargs)) or draft,
    )

    requests = ZenodoRequests(
        "https://sandbox.zenodo.org",
        {"Authorization": "Bearer token"},
    )

    assert requests.create_zenodo_record_version("record-1") is draft
    assert calls == [
        (
            ("record-1",),
            {
                "base_url": "https://sandbox.zenodo.org",
                "headers": {"Authorization": "Bearer token"},
            },
        )
    ]


def test_get_zenodo_record_uses_user_records_to_resolve_state(monkeypatch):
    calls = []
    draft = {"id": "draft-1", "is_published": False}
    monkeypatch.setattr(
        zenodo_module.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs))
        or Response(
            {
                "hits": {
                    "hits": [
                        {"id": "another-record", "is_published": True},
                        draft,
                    ]
                }
            }
        ),
    )

    result = zenodo_module.get_zenodo_record(
        "draft-1",
        base_url="https://zenodo.org",
        headers={"Authorization": "x"},
    )

    assert result is draft
    assert calls[0][0] == ("https://zenodo.org/api/user/records",)
    assert calls[0][1]["params"] == {"q": "id:draft-1", "size": 10}


def test_list_zenodo_user_records_uses_user_records(monkeypatch):
    calls = []
    monkeypatch.setattr(
        zenodo_module.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs))
        or Response({"hits": {"hits": [{"id": "record-1"}]}}),
    )

    result = zenodo_module.list_zenodo_user_records(
        base_url="https://zenodo.org",
        headers={"Authorization": "x"},
        page=2,
        size=25,
    )

    assert result == [{"id": "record-1"}]
    assert calls[0][0] == ("https://zenodo.org/api/user/records",)
    assert calls[0][1]["params"] == {"page": 2, "size": 25}


def test_create_zenodo_record_draft_uses_records_api(monkeypatch):
    calls = []
    monkeypatch.setattr(
        zenodo_module.requests,
        "post",
        lambda *args, **kwargs: calls.append((args, kwargs))
        or Response({"id": "draft-1"}, status_code=201),
    )

    result = zenodo_module.create_zenodo_record_draft(
        base_url="https://zenodo.org",
        headers={"Authorization": "x"},
    )

    assert result == {"id": "draft-1"}
    assert calls[0][0] == ("https://zenodo.org/api/records",)
    assert calls[0][1]["json"] == {"files": {"enabled": True}}


def test_create_version_imports_previous_files(monkeypatch):
    calls = []
    responses = iter(
        [
            Response({"id": "draft-2"}, status_code=201),
            Response({"entries": []}, status_code=201),
        ]
    )
    monkeypatch.setattr(
        zenodo_module.requests,
        "post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or next(responses),
    )

    result = zenodo_module.create_zenodo_record_version(
        "record-1",
        base_url="https://zenodo.org",
        headers={"Authorization": "x"},
    )

    assert result == {"id": "draft-2"}
    assert calls[0][0] == ("https://zenodo.org/api/records/record-1/versions",)
    assert calls[1][0] == (
        "https://zenodo.org/api/records/draft-2/draft/actions/files-import",
    )


def test_upload_zenodo_draft_file_initializes_uploads_and_commits(monkeypatch):
    post_calls = []
    post_responses = iter(
        [
            Response(
                {
                    "entries": [
                        {
                            "key": "results 2026.csv",
                            "links": {
                                "content": (
                                    "/api/records/draft-1/draft/files/"
                                    "results%202026.csv/content"
                                ),
                                "commit": (
                                    "/api/records/draft-1/draft/files/"
                                    "results%202026.csv/commit"
                                ),
                            },
                        }
                    ]
                },
                status_code=201,
            ),
            Response({"key": "results 2026.csv", "status": "completed"}),
        ]
    )
    monkeypatch.setattr(
        zenodo_module.requests,
        "post",
        lambda *args, **kwargs: post_calls.append((args, kwargs))
        or next(post_responses),
    )
    put_calls = []
    monkeypatch.setattr(
        zenodo_module.requests,
        "put",
        lambda *args, **kwargs: put_calls.append((args, kwargs)) or Response({}),
    )

    result = zenodo_module.upload_zenodo_draft_file(
        "/api/records/draft-1/draft/files",
        base_url="https://zenodo.org",
        headers={"Authorization": "x"},
        filename="results 2026.csv",
        content=b"content",
    )

    assert result["status"] == "completed"
    assert post_calls[0][0] == (
        "https://zenodo.org/api/records/draft-1/draft/files",
    )
    assert post_calls[0][1]["json"] == [{"key": "results 2026.csv"}]
    assert put_calls[0][0] == (
        "https://zenodo.org/api/records/draft-1/draft/files/results%202026.csv/content",
    )
    assert put_calls[0][1]["timeout"] == 30
    assert post_calls[1][0] == (
        "https://zenodo.org/api/records/draft-1/draft/files/results%202026.csv/commit",
    )


def test_cancelled_upload_deletes_initialized_file(monkeypatch, tmp_path):
    file_path = tmp_path / "results 2026.csv"
    file_path.write_bytes(b"content")
    delete_calls = []

    monkeypatch.setattr(
        zenodo_requests_module,
        "upload_zenodo_draft_file",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            JobCancelled("Upload canceled")
        ),
    )
    monkeypatch.setattr(
        zenodo_requests_module,
        "delete_zenodo_draft_file",
        lambda *args, **kwargs: delete_calls.append((args, kwargs)),
    )

    requests = ZenodoRequests(
        "https://sandbox.zenodo.org",
        {"Authorization": "x"},
    )

    with pytest.raises(JobCancelled, match="Upload canceled"):
        requests.upload_files_to_draft(
            [file_path],
            "/api/records/draft-1/draft/files",
        )

    assert delete_calls == [
        (
            ("/api/records/draft-1/draft/files",),
            {
                "base_url": "https://sandbox.zenodo.org",
                "headers": {"Authorization": "x"},
                "file_key": "results 2026.csv",
            },
        )
    ]


def test_open_zenodo_file_uses_streaming_response(monkeypatch):
    calls = []
    response = Response()
    response.headers = {}
    monkeypatch.setattr(
        zenodo_module.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or response,
    )

    result = zenodo_module.open_zenodo_file(
        "/api/records/record-1/files/results.csv/content",
        base_url="https://zenodo.org",
        headers={"Authorization": "x"},
    )

    assert result.response is response
    assert calls[0][1]["stream"] is True
    assert calls[0][1]["timeout"] == 30


def test_delete_zenodo_draft_file_uses_draft_files_key(monkeypatch):
    calls = []
    monkeypatch.setattr(
        zenodo_module.requests,
        "delete",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(),
    )

    zenodo_module.delete_zenodo_draft_file(
        "/api/records/draft-1/draft/files",
        base_url="https://sandbox.zenodo.org",
        headers={"Authorization": "x"},
        file_key="results 2026.csv",
    )

    assert calls[0][0] == (
        "https://sandbox.zenodo.org/api/records/draft-1/draft/files/results%202026.csv",
    )
