import json
from types import SimpleNamespace
from unittest.mock import Mock

from zenodo_jupyterlab.routes import (
    ZenodoFileImportCellHandler,
    ZenodoRecordVersionCollectionHandler,
)
from zenodo_jupyterlab.util.sse import EventBus


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
            "file_key": "file-1",
            "status": "active",
            "latest": "true",
        },
    )

    assert response.code == 200
    assert json.loads(response.body) == {"job_ids": []}


def test_import_cell_reuses_file_metadata_for_download_location(tmp_path):
    destination = tmp_path / "123" / "example.csv"
    destination.parent.mkdir()
    destination.touch()
    file_metadata = {"filename": "example.csv"}

    zenodo_requests = Mock()
    zenodo_requests.get_zenodo_record_file.return_value = file_metadata
    download_manager = Mock()
    download_manager.get_download_location_from_metadata.return_value = destination
    responses = []
    handler = SimpleNamespace(
        get_json_body=lambda: {"record_id": "123", "file_key": "example.csv"},
        get_zenodo_requests=lambda _: zenodo_requests,
        get_zenodo_download_manager=lambda _: download_manager,
        finish=responses.append,
    )

    ZenodoFileImportCellHandler.post.__wrapped__(handler)

    zenodo_requests.get_zenodo_record_file.assert_called_once_with(
        record_id="123",
        file_key="example.csv",
    )
    download_manager.get_download_location_from_metadata.assert_called_once_with(
        file_metadata,
        record_id="123",
    )
    assert len(responses) == 1
    assert json.loads(responses[0])["metadata_zenodo_jupyterlab"] == {
        "kind": "import-cell",
        "version": 1,
        "record_id": "123",
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
