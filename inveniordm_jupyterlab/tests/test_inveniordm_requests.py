import pytest
import requests as requests_library

from inveniordm_auth.remote_servers import UnknownRemoteServerError
from inveniordm_auth.token_store import BoundedTokenStore, FileTokenStore
from inveniordm_jupyterlab.util.job_types import JobCancelled
from inveniordm_jupyterlab.inveniordm_file_identifier import InvenioRDMFileIdentifier
from inveniordm_jupyterlab.inveniordm_record_identifier import (
    InvenioRDMRecordIdentifier,
)
from inveniordm_jupyterlab.inveniordm_requests import inveniordm as inveniordm_module
from inveniordm_jupyterlab.inveniordm_requests import (
    inveniordm_requests as inveniordm_requests_module,
)
from inveniordm_jupyterlab.inveniordm_requests.local_inveniordm_requests_factory import (
    LocalInvenioRDMRequestsFactory,
)
from inveniordm_jupyterlab.inveniordm_requests.inveniordm_requests import (
    InvenioRDMRequests,
)


class Response:
    def __init__(self, data=None, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"Unexpected HTTP status {self.status_code}")


def test_local_factory_passes_stored_inveniordm_user_id(tmp_path, remote_servers):
    factory = LocalInvenioRDMRequestsFactory(remote_servers)
    factory.token_store = BoundedTokenStore(FileTokenStore(tmp_path / "tokens.json"))
    factory.token_store.set_token(
        "token",
        True,
        remote_server_id=remote_servers.default.id,
        inveniordm_user_id="123",
    )

    class Handler:
        def get_query_argument(self, name, default=None):
            return default

    requests = factory.create_inveniordm_requests(Handler())

    assert requests.inveniordm_user_id == "123"


def test_local_factory_rejects_unknown_remote_server_override(remote_servers):
    factory = LocalInvenioRDMRequestsFactory(remote_servers)

    class Handler:
        def get_query_argument(self, name, default=None):
            return "removed-server" if name == "remote_server" else default

    with pytest.raises(UnknownRemoteServerError) as raised:
        factory.create_inveniordm_requests(Handler())

    assert raised.value.remote_server_id == "removed-server"


def test_local_factory_rejects_token_for_unknown_remote_server(
    tmp_path, remote_servers
):
    factory = LocalInvenioRDMRequestsFactory(remote_servers)
    factory.token_store = BoundedTokenStore(FileTokenStore(tmp_path / "tokens.json"))
    factory.token_store.set_token(
        "token",
        True,
        remote_server_id="removed-server",
    )

    class Handler:
        def get_query_argument(self, name, default=None):
            return default

    with pytest.raises(UnknownRemoteServerError) as raised:
        factory.create_inveniordm_requests(Handler())

    assert raised.value.remote_server_id == "removed-server"


def test_upload_record_files_passes_record_id(monkeypatch, tmp_path):
    file_path = tmp_path / "results.csv"
    file_path.write_bytes(b"content")
    requests = InvenioRDMRequests(
        "https://sandbox.inveniordm.org", {"Authorization": "x"}
    )
    calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "upload_inveniordm_draft_file",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    assert (
        requests.upload_inveniordm_record_files(
            record_id="draft-1", file_paths=[file_path]
        )
        is None
    )
    assert calls[0][0] == ("draft-1",)
    assert calls[0][1]["base_url"] == "https://sandbox.inveniordm.org"
    assert calls[0][1]["headers"] == {"Authorization": "x"}
    assert calls[0][1]["filename"] == "results.csv"


def test_delete_record_file_passes_file_identifier(monkeypatch):
    requests = InvenioRDMRequests(
        "https://sandbox.inveniordm.org", {"Authorization": "x"}
    )
    calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "delete_inveniordm_draft_file",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    file_id = InvenioRDMFileIdentifier(
        record_id="draft-1",
        record_status="draft",
        file_key="results.csv",
    )

    assert requests.delete_inveniordm_record_file(file_id=file_id) is None
    assert calls == [
        (
            ("draft-1",),
            {
                "base_url": "https://sandbox.inveniordm.org",
                "headers": {"Authorization": "x"},
                "file_key": "results.csv",
            },
        )
    ]


def test_delete_record_draft_uses_authenticated_request(monkeypatch):
    requests = InvenioRDMRequests(
        "https://sandbox.inveniordm.org", {"Authorization": "Bearer token"}
    )
    calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "delete_inveniordm_record_draft",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    assert requests.delete_inveniordm_record_draft("draft-1") is None
    assert calls == [
        (
            ("draft-1",),
            {
                "base_url": "https://sandbox.inveniordm.org",
                "headers": {"Authorization": "Bearer token"},
            },
        )
    ]


def test_create_draft_with_files_passes_only_created_record_id(monkeypatch):
    draft = {"id": "draft-1", "is_published": False}
    requests = InvenioRDMRequests(
        "https://sandbox.inveniordm.org", {"Authorization": "x"}
    )
    calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "create_inveniordm_record_draft",
        lambda **kwargs: draft,
    )
    monkeypatch.setattr(
        requests,
        "upload_inveniordm_record_files",
        lambda **kwargs: calls.append(kwargs),
    )

    assert requests.create_inveniordm_record_draft_with_files(file_paths=[]) is draft
    assert calls == [
        {
            "file_paths": [],
            "record_id": "draft-1",
            "on_upload_progress": None,
            "should_cancel": None,
        }
    ]


def test_create_record_version_uses_authenticated_request(monkeypatch):
    draft = {"id": "draft-2", "is_published": False}
    calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "create_inveniordm_record_version",
        lambda *args, **kwargs: calls.append((args, kwargs)) or draft,
    )

    requests = InvenioRDMRequests(
        "https://sandbox.inveniordm.org",
        {"Authorization": "Bearer token"},
    )

    assert requests.create_inveniordm_record_version("record-1") is draft
    assert calls == [
        (
            ("record-1",),
            {
                "base_url": "https://sandbox.inveniordm.org",
                "headers": {"Authorization": "Bearer token"},
            },
        )
    ]


def test_record_with_grants_has_manage_permission_without_workaround(monkeypatch):
    requests = InvenioRDMRequests(
        "https://inveniordm.org",
        {"Authorization": "x"},
        inveniordm_user_id="58370",
    )
    calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "get_inveniordm_record_public_or_draft",
        lambda record_id, **kwargs: (
            calls.append((record_id, kwargs))
            or {
                "id": record_id,
                "parent": {"access": {"grants": []}},
            }
        ),
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "check_user_record_permission_workaround",
        lambda *args, **kwargs: pytest.fail("permission workaround should not run"),
    )

    assert requests.get_inveniordm_record_permission("123", "draft") == "manage"
    assert calls == [
        (
            "123",
            {
                "record_status": "draft",
                "base_url": "https://inveniordm.org",
                "headers": {"Authorization": "x"},
            },
        )
    ]


@pytest.mark.parametrize(
    ("has_edit", "expected_permission"),
    [(True, "edit"), (False, "preview")],
)
def test_record_without_grants_uses_edit_permission_workaround(
    monkeypatch,
    has_edit,
    expected_permission,
):
    requests = InvenioRDMRequests(
        "https://inveniordm.org",
        {"Authorization": "x"},
        inveniordm_user_id="58370",
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "get_inveniordm_record_public_or_draft",
        lambda record_id, **kwargs: {
            "id": record_id,
            "parent": {"access": {}},
        },
    )
    workaround_calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "check_user_record_permission_workaround",
        lambda **kwargs: workaround_calls.append(kwargs) or has_edit,
    )

    assert (
        requests.get_inveniordm_record_permission("123", "published")
        == expected_permission
    )
    assert workaround_calls == [
        {
            "record_id": "123",
            "user_id": "58370",
            "permission_to_check": "edit",
            "base_url": "https://inveniordm.org",
            "headers": {"Authorization": "x"},
        }
    ]


def test_record_permission_requires_cached_user_id(monkeypatch):
    requests = InvenioRDMRequests("https://inveniordm.org", {"Authorization": "x"})
    monkeypatch.setattr(
        inveniordm_requests_module,
        "get_inveniordm_record_public_or_draft",
        lambda *args, **kwargs: pytest.fail("record should not be fetched"),
    )

    with pytest.raises(
        ValueError,
        match="InvenioRDM user ID is not set. Cannot determine record permission.",
    ):
        requests.get_inveniordm_record_permission("123", "published")


@pytest.mark.parametrize(
    ("records", "expected"), [([{"id": "123"}], True), ([], False)]
)
def test_check_user_record_permission_workaround_queries_encoded_grant_token(
    monkeypatch,
    records,
    expected,
):
    calls = []
    monkeypatch.setattr(
        inveniordm_module,
        "list_inveniordm_user_records",
        lambda **kwargs: calls.append(kwargs) or records,
    )

    assert (
        inveniordm_module.check_user_record_permission_workaround(
            record_id="123",
            user_id="58370",
            permission_to_check="edit",
            base_url="https://inveniordm.org",
            headers={"Authorization": "x"},
        )
        is expected
    )
    assert calls == [
        {
            "base_url": "https://inveniordm.org",
            "headers": {"Authorization": "x"},
            "query": "id:123 AND parent.access.grant_tokens:dXNlcg==.NTgzNzA=.ZWRpdA==",
            "page": 1,
            "size": 1,
        }
    ]


def test_get_inveniordm_record_variant_fetches_requested_record_status(monkeypatch):
    record = {
        "id": "public-123",
        "links": {"files": "https://inveniordm.org/api/records/public-123/files"},
    }
    calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "get_inveniordm_record_public_or_draft",
        lambda *args, **kwargs: calls.append((args, kwargs)) or record,
    )
    requests = InvenioRDMRequests("https://inveniordm.org", {"Authorization": "x"})

    assert (
        requests.get_inveniordm_record_variant(
            InvenioRDMRecordIdentifier(
                record_id="public-123",
                record_status="draft",
            )
        )
        is record
    )
    assert calls == [
        (
            ("public-123",),
            {
                "record_status": "draft",
                "base_url": "https://inveniordm.org",
                "headers": {"Authorization": "x"},
            },
        )
    ]


@pytest.mark.parametrize("include_files", [True, False])
def test_list_inveniordm_user_records_optionally_includes_files(
    monkeypatch, include_files
):
    records = [
        {"id": "draft-123", "is_draft": True},
        {
            "id": "restricted-123",
            "is_draft": False,
            "access": {"files": "restricted"},
        },
    ]
    include_files_calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_user_records",
        lambda *args, **kwargs: records,
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "include_inveniordm_file_if_draft_or_restricted",
        lambda *args, **kwargs: include_files_calls.append((args, kwargs)),
    )

    requests = InvenioRDMRequests("https://inveniordm.org", {"Authorization": "x"})

    assert requests.list_inveniordm_user_records(include_files=include_files) is records
    assert [call[0][0] for call in include_files_calls] == (
        records if include_files else []
    )


@pytest.mark.parametrize("include_files", [True, False])
def test_search_inveniordm_records_optionally_includes_files(
    monkeypatch, include_files
):
    records = {
        "hits": {
            "hits": [
                {"id": "public-123", "access": {"files": "public"}},
                {"id": "restricted-123", "access": {"files": "restricted"}},
            ]
        }
    }
    include_files_calls = []
    monkeypatch.setattr(
        inveniordm_requests_module,
        "search_inveniordm_records",
        lambda *args, **kwargs: records,
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "include_inveniordm_file_if_draft_or_restricted",
        lambda *args, **kwargs: include_files_calls.append((args, kwargs)),
    )

    requests = InvenioRDMRequests("https://inveniordm.org", {"Authorization": "x"})

    assert (
        requests.search_inveniordm_records(query="climate", include_files=include_files)
        is records
    )
    assert [call[0][0] for call in include_files_calls] == (
        records["hits"]["hits"] if include_files else []
    )


def test_search_inveniordm_records_uses_invenio_response_format(monkeypatch):
    calls = []
    response_data = {"hits": {"hits": [{"id": "record-1"}]}}
    monkeypatch.setattr(
        inveniordm_module.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(response_data),
    )

    result = inveniordm_module.search_inveniordm_records(
        "climate",
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
        page=2,
        size=25,
        sort="newest",
        allversions=True,
    )

    assert result is response_data
    assert calls == [
        (
            ("https://inveniordm.org/api/records",),
            {
                "params": {
                    "q": "climate",
                    "page": 2,
                    "size": 25,
                    "sort": "newest",
                    "allversions": True,
                },
                "headers": {
                    "Accept": "application/vnd.inveniordm.v1+json",
                    "Authorization": "x",
                },
                "timeout": 10,
            },
        )
    ]


def test_get_inveniordm_record_public_or_draft_uses_draft_endpoint(monkeypatch):
    calls = []
    draft = {"id": "draft-123", "is_draft": True}
    monkeypatch.setattr(
        inveniordm_module.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(draft),
    )

    result = inveniordm_module.get_inveniordm_record_public_or_draft(
        "draft-123",
        record_status="draft",
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )

    assert result is draft
    assert calls[0][0] == ("https://inveniordm.org/api/records/draft-123/draft",)


def test_list_inveniordm_user_records_uses_user_records(monkeypatch):
    calls = []
    monkeypatch.setattr(
        inveniordm_module.requests,
        "get",
        lambda *args, **kwargs: (
            calls.append((args, kwargs))
            or Response({"hits": {"hits": [{"id": "record-1"}]}})
        ),
    )

    result = inveniordm_module.list_inveniordm_user_records(
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
        page=2,
        size=25,
    )

    assert result == [{"id": "record-1"}]
    assert calls[0][0] == ("https://inveniordm.org/api/user/records",)
    assert calls[0][1]["params"] == {"page": 2, "size": 25}
    assert calls[0][1]["headers"] == {
        "Accept": "application/vnd.inveniordm.v1+json",
        "Authorization": "x",
    }


def test_list_inveniordm_record_versions_uses_versions_endpoint(monkeypatch):
    calls = []
    response_data = {
        "hits": {
            "hits": [
                {"id": "record-1", "versions": {"index": 1}},
                {"id": "record-2", "versions": {"index": 2}},
            ]
        }
    }
    monkeypatch.setattr(
        inveniordm_module.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(response_data),
    )

    result = inveniordm_module.list_inveniordm_record_versions(
        "record/1",
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )

    assert result == response_data
    assert calls[0][0] == ("https://inveniordm.org/api/records/record%2F1/versions",)
    assert calls[0][1]["headers"] == {
        "Accept": "application/vnd.inveniordm.v1+json",
        "Authorization": "x",
    }


def test_record_versions_returns_initial_draft(monkeypatch):
    calls = []
    draft = {
        "id": "draft-1",
        "is_draft": True,
        "parent": {"id": "parent-1"},
        "status": "draft",
        "versions": {"index": 1},
    }
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_record_versions",
        lambda *args, **kwargs: {"hits": {"hits": []}},
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "get_inveniordm_record_public_or_draft",
        lambda *args, **kwargs: calls.append((args, kwargs)) or draft,
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_user_records",
        lambda *args, **kwargs: pytest.fail("should not scan user records"),
    )

    requests = InvenioRDMRequests("https://inveniordm.org", {"Authorization": "x"})

    assert requests.list_inveniordm_record_versions("draft-1") == [draft]
    assert calls == [
        (
            ("draft-1",),
            {
                "record_status": "draft",
                "base_url": "https://inveniordm.org",
                "headers": {"Authorization": "x"},
            },
        )
    ]


@pytest.mark.parametrize("status_code", [401, 403, 404])
def test_empty_record_versions_ignore_missing_draft(monkeypatch, status_code):
    response = requests_library.Response()
    response.status_code = status_code
    error = requests_library.HTTPError(response=response)
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_record_versions",
        lambda *args, **kwargs: {"hits": {"hits": []}},
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "get_inveniordm_record_public_or_draft",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    requests = InvenioRDMRequests("https://inveniordm.org")

    assert requests.list_inveniordm_record_versions("draft-1") == []


def test_empty_record_versions_propagate_other_draft_errors(monkeypatch):
    response = requests_library.Response()
    response.status_code = 500
    error = requests_library.HTTPError(response=response)
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_record_versions",
        lambda *args, **kwargs: {"hits": {"hits": []}},
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "get_inveniordm_record_public_or_draft",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    requests = InvenioRDMRequests("https://inveniordm.org")

    with pytest.raises(requests_library.HTTPError) as raised:
        requests.list_inveniordm_record_versions("draft-1")

    assert raised.value is error


def test_record_versions_preserves_published_and_draft_variants(monkeypatch):
    calls = []
    versions = [
        {
            "id": "518963",
            "parent": {"id": "515274"},
            "status": "published",
            "versions": {"index": 2},
        },
        {
            "id": "515275",
            "parent": {"id": "515274"},
            "status": "published",
            "versions": {"index": 1},
        },
    ]
    new_version_draft = {
        "id": "567677",
        "is_draft": True,
        "parent": {"id": "515274"},
        "status": "new_version_draft",
        "versions": {"index": 3},
    }
    edited_version_draft = {
        "id": "518963",
        "is_draft": True,
        "parent": {"id": "515274"},
        "status": "draft",
        "versions": {"index": 2},
    }
    unrelated_draft = {
        "id": "other-draft",
        "is_draft": True,
        "parent": {"id": "other-parent"},
        "status": "new_version_draft",
        "versions": {"index": 10},
    }
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_record_versions",
        lambda *args, **kwargs: {"hits": {"hits": versions}},
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_user_records",
        lambda *args, **kwargs: (
            calls.append((args, kwargs))
            or [
                *versions,
                new_version_draft,
                edited_version_draft,
                unrelated_draft,
            ]
        ),
    )
    requests = InvenioRDMRequests("https://inveniordm.org", {"Authorization": "x"})

    assert requests.list_inveniordm_record_versions("518963") == [
        versions[0],
        versions[1],
        new_version_draft,
        edited_version_draft,
    ]
    assert calls == [
        (
            (),
            {
                "base_url": "https://inveniordm.org",
                "headers": {"Authorization": "x"},
                "query": "parent.id:515274",
                "size": 25,
                "allversions": True,
            },
        )
    ]


@pytest.mark.parametrize("status_code", [401, 403])
def test_record_versions_ignore_user_records_permission_error(monkeypatch, status_code):
    versions = [
        {
            "id": "518963",
            "parent": {"id": "515274"},
            "status": "published",
        }
    ]
    response = requests_library.Response()
    response.status_code = status_code
    error = requests_library.HTTPError(response=response)
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_record_versions",
        lambda *args, **kwargs: {"hits": {"hits": versions}},
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_user_records",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    requests = InvenioRDMRequests("https://inveniordm.org")

    assert requests.list_inveniordm_record_versions("518963") == versions


def test_record_versions_propagate_other_user_records_errors(monkeypatch):
    versions = [{"id": "518963", "parent": {"id": "515274"}}]
    response = requests_library.Response()
    response.status_code = 500
    error = requests_library.HTTPError(response=response)
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_record_versions",
        lambda *args, **kwargs: {"hits": {"hits": versions}},
    )
    monkeypatch.setattr(
        inveniordm_requests_module,
        "list_inveniordm_user_records",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )

    requests = InvenioRDMRequests("https://inveniordm.org")

    with pytest.raises(requests_library.HTTPError) as raised:
        requests.list_inveniordm_record_versions("518963")

    assert raised.value is error


def test_create_inveniordm_record_draft_uses_records_api(monkeypatch):
    calls = []
    draft = {
        "id": "draft-1",
        "is_published": False,
        "links": {
            "files": "https://inveniordm.org/api/records/draft-1/draft/files",
            "self_html": "https://inveniordm.org/uploads/draft-1",
        },
    }
    monkeypatch.setattr(
        inveniordm_module.requests,
        "post",
        lambda *args, **kwargs: (
            calls.append((args, kwargs)) or Response(draft, status_code=201)
        ),
    )

    result = inveniordm_module.create_inveniordm_record_draft(
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )

    assert result is draft
    assert calls[0][0] == ("https://inveniordm.org/api/records",)
    assert calls[0][1]["json"] == {"files": {"enabled": True}}
    assert calls[0][1]["headers"] == {
        "Accept": "application/vnd.inveniordm.v1+json",
        "Content-Type": "application/json",
        "Authorization": "x",
    }


def test_create_version_imports_previous_files(monkeypatch):
    calls = []
    draft = {
        "id": "draft-2",
        "is_published": False,
        "links": {
            "files": "https://inveniordm.org/api/records/draft-2/draft/files",
            "self_html": "https://inveniordm.org/uploads/draft-2",
        },
    }
    responses = iter(
        [
            Response(draft, status_code=201),
            Response({"entries": []}, status_code=201),
        ]
    )
    monkeypatch.setattr(
        inveniordm_module.requests,
        "post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or next(responses),
    )

    result = inveniordm_module.create_inveniordm_record_version(
        "record-1",
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )

    assert result is draft
    assert result["files"] == {"entries": []}
    assert calls[0][0] == ("https://inveniordm.org/api/records/record-1/versions",)
    assert calls[0][1]["headers"] == {
        "Accept": "application/vnd.inveniordm.v1+json",
        "Authorization": "x",
    }
    assert calls[1][0] == (
        "https://inveniordm.org/api/records/draft-2/draft/actions/files-import",
    )


def test_upload_inveniordm_draft_file_initializes_uploads_and_commits(monkeypatch):
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
        inveniordm_module.requests,
        "post",
        lambda *args, **kwargs: (
            post_calls.append((args, kwargs)) or next(post_responses)
        ),
    )
    put_calls = []
    monkeypatch.setattr(
        inveniordm_module.requests,
        "put",
        lambda *args, **kwargs: put_calls.append((args, kwargs)) or Response({}),
    )

    result = inveniordm_module.upload_inveniordm_draft_file(
        "draft-1",
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
        filename="results 2026.csv",
        content=b"content",
    )

    assert result["status"] == "completed"
    assert post_calls[0][0] == (
        "https://inveniordm.org/api/records/draft-1/draft/files",
    )
    assert post_calls[0][1]["json"] == [{"key": "results 2026.csv"}]
    assert put_calls[0][0] == (
        "https://inveniordm.org/api/records/draft-1/draft/files/results%202026.csv/content",
    )
    assert put_calls[0][1]["timeout"] == 30
    assert post_calls[1][0] == (
        "https://inveniordm.org/api/records/draft-1/draft/files/results%202026.csv/commit",
    )


def test_cancelled_upload_deletes_initialized_file(monkeypatch, tmp_path):
    file_path = tmp_path / "results 2026.csv"
    file_path.write_bytes(b"content")
    delete_calls = []
    requests = InvenioRDMRequests(
        "https://sandbox.inveniordm.org",
        {"Authorization": "x"},
    )

    monkeypatch.setattr(
        inveniordm_requests_module,
        "upload_inveniordm_draft_file",
        lambda *args, **kwargs: (_ for _ in ()).throw(JobCancelled("Upload canceled")),
    )
    monkeypatch.setattr(
        requests,
        "delete_inveniordm_record_file",
        lambda **kwargs: delete_calls.append(kwargs),
    )

    with pytest.raises(JobCancelled, match="Upload canceled"):
        requests.upload_inveniordm_record_files(
            file_paths=[file_path],
            record_id="draft-1",
        )

    assert delete_calls == [
        {
            "file_id": InvenioRDMFileIdentifier(
                record_id="draft-1",
                record_status="draft",
                file_key="results 2026.csv",
            )
        }
    ]


@pytest.mark.parametrize(
    ("record_status", "variant_path"),
    [("draft", "draft/files"), ("published", "files")],
)
def test_open_inveniordm_file_uses_direct_content_endpoint(
    monkeypatch, record_status, variant_path
):
    calls = []
    response = Response()
    response.headers = {}
    monkeypatch.setattr(
        inveniordm_module.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or response,
    )

    result = inveniordm_module.open_inveniordm_file(
        InvenioRDMFileIdentifier(
            record_id="565160",
            record_status=record_status,
            file_key="Devoir 2.docx",
        ),
        base_url="https://inveniordm.org",
        headers={"Authorization": "x"},
    )

    assert result.response is response
    assert calls[0][0] == (
        f"https://inveniordm.org/api/records/565160/{variant_path}/Devoir%202.docx/content",
    )
    assert calls[0][1]["stream"] is True
    assert calls[0][1]["timeout"] == 30


def test_delete_inveniordm_draft_file_uses_draft_files_key(monkeypatch):
    calls = []
    monkeypatch.setattr(
        inveniordm_module.requests,
        "delete",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(),
    )

    inveniordm_module.delete_inveniordm_draft_file(
        "draft-1",
        base_url="https://sandbox.inveniordm.org",
        headers={"Authorization": "x"},
        file_key="results 2026.csv",
    )

    assert calls[0][0] == (
        "https://sandbox.inveniordm.org/api/records/draft-1/draft/files/results%202026.csv",
    )


def test_delete_inveniordm_record_draft_uses_draft_endpoint(monkeypatch):
    calls = []
    monkeypatch.setattr(
        inveniordm_module.requests,
        "delete",
        lambda *args, **kwargs: (
            calls.append((args, kwargs)) or Response(status_code=204)
        ),
    )

    inveniordm_module.delete_inveniordm_record_draft(
        "draft / 1",
        base_url="https://sandbox.inveniordm.org/",
        headers={"Authorization": "Bearer token"},
    )

    assert calls == [
        (
            ("https://sandbox.inveniordm.org/api/records/draft%20%2F%201/draft",),
            {
                "headers": {
                    "Accept": "application/vnd.inveniordm.v1+json",
                    "Authorization": "Bearer token",
                },
                "timeout": 10,
            },
        )
    ]
