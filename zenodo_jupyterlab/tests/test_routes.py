import json
from types import SimpleNamespace
from unittest.mock import Mock

from zenodo_jupyterlab.routes import (
    ZenodoFileImportCellHandler,
    ZenodoRecordCollectionHandler,
    ZenodoRecordVersionCollectionHandler,
)
from zenodo_jupyterlab.util.sse import EventBus
from zenodo_jupyterlab.zenodo_file_identifier import ZenodoFileIdentifier


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
    draft = {
        "id": "draft-2",
        "status": "new_version_draft",
        "files": {"entries": [{"key": "data.csv"}]},
    }
    zenodo_requests = Mock()
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

    event = events.get_nowait()
    assert event.topic == "record.changed.record-1"
    assert event.data == {
        "type": "version_created",
        "record": draft,
    }
    assert json.loads(responses[0]) == {"draft": draft}
