import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from zenodo_jupyterlab.routes import (
    ZenodoFileImportCellHandler,
    ZenodoRecordCollectionHandler,
    ZenodoRecordPermissionHandler,
    ZenodoRecordVariantItemHandler,
    ZenodoRecordVersionCollectionHandler,
    ZenodoUserRecordItemHandler,
)
from zenodo_jupyterlab.util.sse import EventBus
from zenodo_jupyterlab.zenodo_file_identifier import ZenodoFileIdentifier
from zenodo_jupyterlab.zenodo_record_identifier import ZenodoRecordIdentifier


async def test_hello(jp_fetch):
    # When
    response = await jp_fetch("zenodo-jupyterlab", "hello")

    # Then
    assert response.code == 200
    payload = json.loads(response.body)
    assert payload == {
        "data": (
            "Hello, world!"
            " This is the '/zenodo-jupyterlab/hello' endpoint."
            " Try visiting me in your browser!"
        ),
    }


async def test_cancel_unknown_job(jp_fetch):
    response = await jp_fetch(
        "zenodo-jupyterlab",
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
        "zenodo-jupyterlab",
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
        "zenodo-jupyterlab",
        "user",
        "records",
        "record-1",
        raise_error=False,
    )

    assert response.code == 405


async def test_get_record_item_route_is_not_registered(jp_fetch):
    response = await jp_fetch(
        "zenodo-jupyterlab",
        "records",
        "record-1",
        raise_error=False,
    )

    assert response.code == 404


async def test_list_record_versions_passes_include_drafts():
    zenodo_requests = Mock()
    zenodo_requests.list_zenodo_record_versions.return_value = []
    responses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: "false",
        get_zenodo_requests=lambda _: zenodo_requests,
        finish=responses.append,
    )

    await ZenodoRecordVersionCollectionHandler.get.__wrapped__(handler, "record-1")

    zenodo_requests.list_zenodo_record_versions.assert_called_once_with(
        "record-1", include_drafts=False
    )
    assert json.loads(responses[0]) == []


def test_get_record_variant_passes_record_identifier():
    zenodo_requests = Mock()
    zenodo_requests.get_zenodo_record_variant.return_value = {"id": "record-1"}
    responses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: "draft",
        get_zenodo_requests=lambda _: zenodo_requests,
        finish=responses.append,
    )

    ZenodoRecordVariantItemHandler.get.__wrapped__(handler, "record-1")

    zenodo_requests.get_zenodo_record_variant.assert_called_once_with(
        ZenodoRecordIdentifier(record_id="record-1", record_status="draft")
    )
    assert json.loads(responses[0]) == {"id": "record-1"}


@pytest.mark.parametrize("record_status", [None, "unknown"])
def test_get_record_variant_requires_known_record_status(record_status):
    zenodo_requests = Mock()
    responses = []
    statuses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: record_status,
        get_zenodo_requests=lambda _: zenodo_requests,
        set_status=statuses.append,
        finish=responses.append,
    )

    ZenodoRecordVariantItemHandler.get.__wrapped__(handler, "record-1")

    assert statuses == [400]
    assert json.loads(responses[0]) == {
        "message": "record_status must be 'draft' or 'published'"
    }
    zenodo_requests.get_zenodo_record_variant.assert_not_called()


async def test_record_permission_passes_record_status():
    zenodo_requests = Mock()
    zenodo_requests.get_zenodo_record_permission.return_value = "manage"
    responses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: "draft",
        get_zenodo_requests=lambda _: zenodo_requests,
        finish=responses.append,
    )

    await ZenodoRecordPermissionHandler.get.__wrapped__(handler, "record-1")

    zenodo_requests.get_zenodo_record_permission.assert_called_once_with(
        "record-1", "draft"
    )
    assert json.loads(responses[0]) == "manage"


async def test_record_permission_rejects_missing_record_status():
    zenodo_requests = Mock()
    responses = []
    statuses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: default,
        get_zenodo_requests=lambda _: zenodo_requests,
        set_status=statuses.append,
        finish=responses.append,
    )

    await ZenodoRecordPermissionHandler.get.__wrapped__(handler, "record-1")

    assert statuses == [400]
    assert json.loads(responses[0]) == {
        "message": "record_status must be 'draft' or 'published'"
    }
    zenodo_requests.get_zenodo_record_permission.assert_not_called()


def test_delete_user_record_discards_draft():
    zenodo_requests = Mock()
    zenodo_requests.get_zenodo_record_variant.return_value = {
        "id": "draft-1",
        "parent": {"id": "parent-1"},
    }
    published = {"id": "record-1", "versions": {"index": 1}}
    draft = {"id": "draft-1", "versions": {"index": 2}}
    zenodo_requests.list_zenodo_record_versions.return_value = [published, draft]
    event_bus = EventBus()
    events = event_bus.subscribe("alice")
    responses = []
    statuses = []
    handler = SimpleNamespace(
        current_user=SimpleNamespace(username="alice"),
        event_bus=event_bus,
        get_zenodo_requests=lambda _: zenodo_requests,
        set_status=statuses.append,
        finish=lambda value=None: responses.append(value),
    )

    ZenodoUserRecordItemHandler.delete.__wrapped__(handler, "draft-1")

    zenodo_requests.get_zenodo_record_variant.assert_called_once_with(
        ZenodoRecordIdentifier(record_id="draft-1", record_status="draft")
    )
    zenodo_requests.list_zenodo_record_versions.assert_called_once_with(
        "draft-1", include_drafts=True
    )
    zenodo_requests.delete_zenodo_record_draft.assert_called_once_with("draft-1")
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
    zenodo_requests = Mock()
    zenodo_requests.get_zenodo_record_variant.return_value = {
        "id": "draft-1",
        "parent": {"id": ""},
    }
    zenodo_requests.list_zenodo_record_versions.return_value = [
        {"id": "draft-1", "versions": {"index": 1}}
    ]
    event_bus = EventBus()
    events = event_bus.subscribe("alice")
    handler = SimpleNamespace(
        current_user=SimpleNamespace(username="alice"),
        event_bus=event_bus,
        get_zenodo_requests=lambda _: zenodo_requests,
        set_status=lambda _: None,
        finish=lambda value=None: None,
    )

    ZenodoUserRecordItemHandler.delete.__wrapped__(handler, "draft-1")

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
    zenodo_requests = Mock()
    zenodo_requests.search_zenodo_records.return_value = {"hits": {"hits": []}}
    responses = []
    query_arguments = {"q": "climate", "include_files": "true"}
    handler = SimpleNamespace(
        get_query_argument=lambda name, default: query_arguments.get(name, default),
        get_zenodo_requests=lambda _: zenodo_requests,
        finish=responses.append,
    )

    ZenodoRecordCollectionHandler.get.__wrapped__(handler)

    zenodo_requests.search_zenodo_records.assert_called_once_with(
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
    zenodo_requests = Mock()
    download_manager = Mock()
    download_manager.get_download_location.return_value = destination
    responses = []
    handler = SimpleNamespace(
        get_json_body=lambda: {
            "record_id": "123",
            "record_status": "draft",
            "file_key": "example.csv",
        },
        get_zenodo_requests=lambda _: zenodo_requests,
        get_zenodo_download_manager=lambda _: download_manager,
        finish=responses.append,
    )

    ZenodoFileImportCellHandler.post.__wrapped__(handler)

    zenodo_requests.get_zenodo_record_file.assert_not_called()
    download_manager.get_download_location.assert_called_once_with(
        file_id=ZenodoFileIdentifier(
            record_id="123",
            record_status="draft",
            file_key="example.csv",
        ),
    )
    assert len(responses) == 1
    assert json.loads(responses[0])["metadata_zenodo_jupyterlab"] == {
        "kind": "import-cell",
        "version": 1,
        "record_id": "123",
        "record_status": "draft",
        "file_key": "example.csv",
        "path": str(destination),
    }


def test_create_version_event_contains_new_draft():
    published = {"id": "record-1", "versions": {"index": 1}}
    draft = {
        "id": "draft-2",
        "status": "new_version_draft",
        "parent": {"id": "parent-1"},
        "versions": {"index": 2},
        "files": {"entries": [{"key": "data.csv"}]},
    }
    zenodo_requests = Mock()
    zenodo_requests.list_zenodo_record_versions.return_value = [published]
    zenodo_requests.create_zenodo_record_version.return_value = draft
    event_bus = EventBus()
    events = event_bus.subscribe("alice")
    responses = []
    handler = SimpleNamespace(
        current_user=SimpleNamespace(username="alice"),
        event_bus=event_bus,
        get_zenodo_requests=lambda _: zenodo_requests,
        finish=responses.append,
    )

    ZenodoRecordVersionCollectionHandler.post.__wrapped__(handler, "record-1")

    zenodo_requests.list_zenodo_record_versions.assert_called_once_with(
        "record-1", include_drafts=True
    )
    zenodo_requests.create_zenodo_record_version.assert_called_once_with("record-1")
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
