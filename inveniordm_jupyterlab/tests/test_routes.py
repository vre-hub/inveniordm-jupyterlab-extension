import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from inveniordm_jupyterlab import routes
from inveniordm_auth.remote_servers import RemoteServerRegistry
from inveniordm_jupyterlab.routes import (
    InvenioRDMCurrentRemoteServerHandler,
    InvenioRDMFileImportCellHandler,
    InvenioRDMRecordCollectionHandler,
    InvenioRDMRecordPermissionHandler,
    InvenioRDMRecordVariantItemHandler,
    InvenioRDMRecordVersionCollectionHandler,
    InvenioRDMRemoteServersHandler,
    InvenioRDMUserRecordItemHandler,
)
from inveniordm_jupyterlab.util.sse import EventBus
from inveniordm_jupyterlab.inveniordm_file_identifier import InvenioRDMFileIdentifier
from inveniordm_jupyterlab.inveniordm_record_identifier import (
    InvenioRDMRecordIdentifier,
)


def test_setup_route_handlers_uses_configured_request_mode(monkeypatch, remote_servers):
    factory = Mock()
    create_factory = Mock(return_value=factory)
    monkeypatch.setattr(routes, "create_inveniordm_requests_factory", create_factory)
    web_app = SimpleNamespace(
        settings={"base_url": "/"},
        add_handlers=Mock(),
    )

    routes.setup_route_handlers(web_app, remote_servers, "proxy")

    create_factory.assert_called_once_with(remote_servers, "proxy")


async def test_hello(jp_fetch):
    # When
    response = await jp_fetch("inveniordm-jupyterlab", "hello")

    # Then
    assert response.code == 200
    payload = json.loads(response.body)
    assert payload == {
        "data": (
            "Hello, world!"
            " This is the '/inveniordm-jupyterlab/hello' endpoint."
            " Try visiting me in your browser!"
        ),
    }


@pytest.mark.parametrize(
    "path",
    [
        ("access-token",),
        ("me",),
        ("user", "records"),
    ],
)
async def test_unknown_remote_server_returns_bad_request(jp_fetch, path):
    response = await jp_fetch(
        "inveniordm-jupyterlab",
        *path,
        params={"remote_server": "removed-server"},
        raise_error=False,
    )

    assert response.code == 400
    assert json.loads(response.body)["message"] == (
        "Unknown remote server: removed-server"
    )


def test_get_current_remote_server(remote_servers):
    responses = []
    inveniordm_requests = Mock()
    factory = SimpleNamespace(
        create_inveniordm_requests=Mock(return_value=inveniordm_requests),
        get_remote_server_id=Mock(return_value=remote_servers.default.id),
        remote_servers=remote_servers,
    )
    handler = SimpleNamespace(
        inveniordm_requests_factory=factory,
        finish=responses.append,
    )

    InvenioRDMCurrentRemoteServerHandler.get.__wrapped__(handler)

    factory.create_inveniordm_requests.assert_called_once_with(handler)
    factory.get_remote_server_id.assert_called_once_with(inveniordm_requests)
    assert json.loads(responses[0]) == {
        "id": remote_servers.default.id,
        "display_name": remote_servers.default.label,
    }


def test_remote_servers_report_local_login_availability(remote_servers):
    responses = []
    handler = SimpleNamespace(
        remote_servers=remote_servers,
        request_mode="local",
        finish=responses.append,
    )

    InvenioRDMRemoteServersHandler.get.__wrapped__(handler)

    payload = json.loads(responses[0])
    assert all(server["login_available"] for server in payload)


def test_remote_servers_report_when_local_login_is_unavailable():
    remote_servers = RemoteServerRegistry(
        {
            "public_repository": {
                "label": "Public repository",
                "base_url": "https://public.example",
            }
        }
    )
    responses = []
    handler = SimpleNamespace(
        remote_servers=remote_servers,
        request_mode="local",
        finish=responses.append,
    )

    InvenioRDMRemoteServersHandler.get.__wrapped__(handler)

    assert json.loads(responses[0]) == [
        {
            "id": "public_repository",
            "label": "Public repository",
            "login_available": False,
        }
    ]


async def test_cancel_unknown_job(jp_fetch):
    response = await jp_fetch(
        "inveniordm-jupyterlab",
        "jobs",
        "unknown",
        "cancel",
        method="POST",
        body="",
        raise_error=False,
    )

    assert response.code == 404
    assert json.loads(response.body) == {"message": "Unknown job"}


async def test_find_active_download_jobs(jp_fetch):
    response = await jp_fetch(
        "inveniordm-jupyterlab",
        "jobs",
        params={
            "job_type": "download",
            "record_id": "123",
            "record_status": "draft",
            "file_key": "file-1",
            "status": "active",
            "latest": "true",
        },
    )

    assert response.code == 200
    assert json.loads(response.body) == {"job_ids": []}


async def test_get_user_record_is_not_supported(jp_fetch):
    response = await jp_fetch(
        "inveniordm-jupyterlab",
        "user",
        "records",
        "record-1",
        raise_error=False,
    )

    assert response.code == 405


async def test_get_record_item_route_is_not_registered(jp_fetch):
    response = await jp_fetch(
        "inveniordm-jupyterlab",
        "records",
        "record-1",
        raise_error=False,
    )

    assert response.code == 404


async def test_list_record_versions_passes_include_drafts():
    inveniordm_requests = Mock()
    inveniordm_requests.list_inveniordm_record_versions.return_value = []
    responses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: "false",
        get_inveniordm_requests=lambda _: inveniordm_requests,
        finish=responses.append,
    )

    await InvenioRDMRecordVersionCollectionHandler.get.__wrapped__(handler, "record-1")

    inveniordm_requests.list_inveniordm_record_versions.assert_called_once_with(
        "record-1", include_drafts=False
    )
    assert json.loads(responses[0]) == []


def test_get_record_variant_passes_record_identifier():
    inveniordm_requests = Mock()
    inveniordm_requests.get_inveniordm_record_variant.return_value = {"id": "record-1"}
    responses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: "draft",
        get_inveniordm_requests=lambda _: inveniordm_requests,
        finish=responses.append,
    )

    InvenioRDMRecordVariantItemHandler.get.__wrapped__(handler, "record-1")

    inveniordm_requests.get_inveniordm_record_variant.assert_called_once_with(
        InvenioRDMRecordIdentifier(record_id="record-1", record_status="draft")
    )
    assert json.loads(responses[0]) == {"id": "record-1"}


@pytest.mark.parametrize("record_status", [None, "unknown"])
def test_get_record_variant_requires_known_record_status(record_status):
    inveniordm_requests = Mock()
    responses = []
    statuses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: record_status,
        get_inveniordm_requests=lambda _: inveniordm_requests,
        set_status=statuses.append,
        finish=responses.append,
    )

    InvenioRDMRecordVariantItemHandler.get.__wrapped__(handler, "record-1")

    assert statuses == [400]
    assert json.loads(responses[0]) == {
        "message": "record_status must be 'draft' or 'published'"
    }
    inveniordm_requests.get_inveniordm_record_variant.assert_not_called()


async def test_record_permission_passes_record_status():
    inveniordm_requests = Mock()
    inveniordm_requests.get_inveniordm_record_permission.return_value = "manage"
    responses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: "draft",
        get_inveniordm_requests=lambda _: inveniordm_requests,
        finish=responses.append,
    )

    await InvenioRDMRecordPermissionHandler.get.__wrapped__(handler, "record-1")

    inveniordm_requests.get_inveniordm_record_permission.assert_called_once_with(
        "record-1", "draft"
    )
    assert json.loads(responses[0]) == "manage"


async def test_record_permission_rejects_missing_record_status():
    inveniordm_requests = Mock()
    responses = []
    statuses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: default,
        get_inveniordm_requests=lambda _: inveniordm_requests,
        set_status=statuses.append,
        finish=responses.append,
    )

    await InvenioRDMRecordPermissionHandler.get.__wrapped__(handler, "record-1")

    assert statuses == [400]
    assert json.loads(responses[0]) == {
        "message": "record_status must be 'draft' or 'published'"
    }
    inveniordm_requests.get_inveniordm_record_permission.assert_not_called()


def test_delete_user_record_discards_draft():
    inveniordm_requests = Mock()
    inveniordm_requests.get_inveniordm_record_variant.return_value = {
        "id": "draft-1",
        "parent": {"id": "parent-1"},
    }
    published = {
        "id": "draft-1",
        "is_draft": False,
        "versions": {"index": 1},
    }
    draft = {"id": "draft-1", "is_draft": True, "versions": {"index": 1}}
    inveniordm_requests.list_inveniordm_record_versions.return_value = [
        published,
        draft,
    ]
    event_bus = EventBus()
    events = event_bus.subscribe("alice")
    responses = []
    statuses = []
    handler = SimpleNamespace(
        current_user=SimpleNamespace(username="alice"),
        event_bus=event_bus,
        get_inveniordm_requests=lambda _: inveniordm_requests,
        set_status=statuses.append,
        finish=lambda value=None: responses.append(value),
    )

    InvenioRDMUserRecordItemHandler.delete.__wrapped__(handler, "draft-1")

    inveniordm_requests.get_inveniordm_record_variant.assert_called_once_with(
        InvenioRDMRecordIdentifier(record_id="draft-1", record_status="draft")
    )
    inveniordm_requests.list_inveniordm_record_versions.assert_called_once_with(
        "draft-1", include_drafts=True
    )
    inveniordm_requests.delete_inveniordm_record_draft.assert_called_once_with(
        "draft-1"
    )
    event = events.get_nowait()
    assert event.topic == "record.versions.changed"
    assert event.data == {
        "type": "draft_discarded",
        "record_id": "draft-1",
        "discarded_draft_id": "draft-1",
        "parent_id": "parent-1",
        "versions": [published],
    }
    assert statuses == [204]
    assert responses == [None]


def test_delete_initial_draft_publishes_versions_event_without_parent():
    inveniordm_requests = Mock()
    inveniordm_requests.get_inveniordm_record_variant.return_value = {
        "id": "draft-1",
        "parent": {"id": ""},
    }
    inveniordm_requests.list_inveniordm_record_versions.return_value = [
        {"id": "draft-1", "is_draft": True, "versions": {"index": 1}}
    ]
    event_bus = EventBus()
    events = event_bus.subscribe("alice")
    handler = SimpleNamespace(
        current_user=SimpleNamespace(username="alice"),
        event_bus=event_bus,
        get_inveniordm_requests=lambda _: inveniordm_requests,
        set_status=lambda _: None,
        finish=lambda value=None: None,
    )

    InvenioRDMUserRecordItemHandler.delete.__wrapped__(handler, "draft-1")

    event = events.get_nowait()
    assert event.topic == "record.versions.changed"
    assert event.data == {
        "type": "draft_discarded",
        "record_id": "draft-1",
        "discarded_draft_id": "draft-1",
        "parent_id": None,
        "versions": [],
    }


def test_search_records_passes_include_files():
    inveniordm_requests = Mock()
    inveniordm_requests.search_inveniordm_records.return_value = {"hits": {"hits": []}}
    responses = []
    query_arguments = {"q": "climate", "include_files": "true"}
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: query_arguments.get(name, default),
        get_inveniordm_requests=lambda _: inveniordm_requests,
        finish=responses.append,
    )

    InvenioRDMRecordCollectionHandler.get.__wrapped__(handler)

    inveniordm_requests.search_inveniordm_records.assert_called_once_with(
        query="climate",
        page=1,
        size=10,
        sort="bestmatch",
        allversions=False,
        include_files=True,
    )
    assert json.loads(responses[0]) == {"hits": {"hits": []}}


def test_import_cell_constructs_download_location_without_metadata_lookup(tmp_path):
    destination = tmp_path / "123" / "draft" / "example.csv"
    destination.parent.mkdir(parents=True)
    destination.touch()
    inveniordm_requests = Mock()
    download_manager = Mock()
    download_manager.get_download_location.return_value = destination
    responses = []
    handler = SimpleNamespace(
        get_json_body=lambda: {
            "record_id": "123",
            "record_status": "draft",
            "file_key": "example.csv",
        },
        get_inveniordm_requests=lambda _: inveniordm_requests,
        get_inveniordm_download_manager=lambda _: download_manager,
        finish=responses.append,
    )

    InvenioRDMFileImportCellHandler.post.__wrapped__(handler)

    inveniordm_requests.get_inveniordm_record_file.assert_not_called()
    download_manager.get_download_location.assert_called_once_with(
        file_id=InvenioRDMFileIdentifier(
            record_id="123",
            record_status="draft",
            file_key="example.csv",
        ),
    )
    assert len(responses) == 1
    assert json.loads(responses[0])["metadata_inveniordm_jupyterlab"] == {
        "kind": "import-cell",
        "version": 1,
        "record_id": "123",
        "record_status": "draft",
        "file_key": "example.csv",
        "path": str(destination),
    }


def test_create_version_event_contains_new_draft():
    published = {
        "id": "draft-2",
        "is_draft": False,
        "versions": {"index": 2},
    }
    stale_draft = {
        "id": "draft-2",
        "is_draft": True,
        "versions": {"index": 2},
    }
    draft = {
        "id": "draft-2",
        "is_draft": True,
        "status": "new_version_draft",
        "parent": {"id": "parent-1"},
        "versions": {"index": 2},
        "files": {"entries": [{"key": "data.csv"}]},
    }
    inveniordm_requests = Mock()
    inveniordm_requests.list_inveniordm_record_versions.return_value = [
        published,
        stale_draft,
    ]
    inveniordm_requests.create_inveniordm_record_version.return_value = draft
    event_bus = EventBus()
    events = event_bus.subscribe("alice")
    responses = []
    handler = SimpleNamespace(
        current_user=SimpleNamespace(username="alice"),
        event_bus=event_bus,
        get_inveniordm_requests=lambda _: inveniordm_requests,
        finish=responses.append,
    )

    InvenioRDMRecordVersionCollectionHandler.post.__wrapped__(handler, "record-1")

    inveniordm_requests.list_inveniordm_record_versions.assert_called_once_with(
        "record-1", include_drafts=True
    )
    inveniordm_requests.create_inveniordm_record_version.assert_called_once_with(
        "record-1"
    )
    event = events.get_nowait()
    assert event.topic == "record.versions.changed"
    assert event.data == {
        "type": "version_created",
        "record_id": "record-1",
        "parent_id": "parent-1",
        "record": draft,
        "versions": [published, draft],
    }
    assert json.loads(responses[0]) == {"draft": draft}
