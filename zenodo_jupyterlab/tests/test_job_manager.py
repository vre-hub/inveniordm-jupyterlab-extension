import asyncio
from io import BytesIO
from threading import Event

import pytest

from zenodo_jupyterlab.util.job_manager import JobManager
from zenodo_jupyterlab.util.job_types import JobCancelled, JobProgress
from zenodo_jupyterlab.zenodo_requests.zenodo_requests import (
    ProgressReportingReader,
)


async def wait_for_terminal_progress(
    manager: JobManager,
    job_id: str,
) -> dict[str, object]:
    for _ in range(100):
        progress = manager.get_progress(job_id)
        assert progress is not None
        if progress["status"] in {"done", "error", "canceled"}:
            return progress
        await asyncio.sleep(0.01)
    raise AssertionError("Job did not finish")


@pytest.mark.asyncio
async def test_upload_job_reports_progress_and_result():
    manager = JobManager()
    progress_events = []

    def upload(context):
        context.update(
            completed_bytes=4,
            total_bytes=10,
            current_item="data.csv",
        )
        return {"draft": {"id": 123}}

    upload_id = manager.start(
        upload,
        progress=JobProgress(job_type="upload"),
        on_progress_changed=lambda job_id, progress: progress_events.append(
            (job_id, progress)
        ),
    )

    progress = await wait_for_terminal_progress(manager, upload_id)
    await asyncio.sleep(0)

    assert progress == {
        "job_type": "upload",
        "metadata": {},
        "job_id": upload_id,
        "status": "done",
        "completed_bytes": 4,
        "total_bytes": 10,
        "current_item": "data.csv",
        "message": None,
        "result": {"draft": {"id": 123}},
        "cancel_requested": False,
    }
    assert progress_events[-1] == (upload_id, progress)


@pytest.mark.asyncio
async def test_download_job_uses_common_progress_shape():
    manager = JobManager()

    def download(context):
        context.update(completed_bytes=5, total_bytes=None)
        return {"path": "/tmp/data.csv"}

    download_id = manager.start(
        download,
        progress=JobProgress(job_type="download"),
    )
    progress = await wait_for_terminal_progress(manager, download_id)

    assert progress == {
        "job_type": "download",
        "metadata": {},
        "job_id": download_id,
        "status": "done",
        "completed_bytes": 5,
        "total_bytes": None,
        "current_item": None,
        "message": None,
        "result": {"path": "/tmp/data.csv"},
        "cancel_requested": False,
    }


@pytest.mark.asyncio
async def test_cancel_pending_job_does_not_run_it():
    manager = JobManager()
    was_run = False

    def job(context):
        nonlocal was_run
        was_run = True
        return {}

    job_id = manager.start(
        job,
        progress=JobProgress(job_type="upload"),
        cancel_message="Upload canceled",
    )
    cancel_progress = manager.cancel(job_id)
    progress = await wait_for_terminal_progress(manager, job_id)

    assert cancel_progress is not None
    assert cancel_progress["status"] == "canceling"
    assert progress["status"] == "canceled"
    assert progress["cancel_requested"] is True
    assert progress["message"] == "Upload canceled"
    assert was_run is False


@pytest.mark.asyncio
async def test_cancel_running_job_is_reported_as_canceled():
    manager = JobManager()
    started = Event()
    continue_job = Event()

    def job(context):
        started.set()
        continue_job.wait(timeout=1)
        if context.should_cancel():
            raise JobCancelled("Upload canceled")
        return {"draft": {"id": 123}}

    job_id = manager.start(job, progress=JobProgress(job_type="upload"))
    assert await asyncio.to_thread(started.wait, 1)

    cancel_progress = manager.cancel(job_id)
    continue_job.set()
    progress = await wait_for_terminal_progress(manager, job_id)

    assert cancel_progress is not None
    assert cancel_progress["status"] == "canceling"
    assert progress["status"] == "canceled"
    assert progress["message"] == "Upload canceled"


@pytest.mark.asyncio
async def test_job_error_is_stored():
    manager = JobManager()

    def job(context):
        raise ValueError("Could not transfer file")

    job_id = manager.start(job, progress=JobProgress(job_type="download"))
    progress = await wait_for_terminal_progress(manager, job_id)

    assert progress["status"] == "error"
    assert progress["message"] == "Could not transfer file"


def test_cancel_unknown_job_returns_none():
    assert JobManager().cancel("unknown") is None


def test_find_progress_filters_metadata_and_returns_latest_first():
    manager = JobManager()
    first_id = manager.progress_store.create(
        JobProgress(
            job_type="download",
            metadata={"record_id": "123", "file_key": "file-1"},
        )
    )
    latest_id = manager.progress_store.create(
        JobProgress(
            job_type="download",
            metadata={"record_id": "123", "file_key": "file-1"},
        )
    )
    manager.progress_store.create(
        JobProgress(
            job_type="download",
            metadata={"record_id": "other", "file_key": "file-1"},
        )
    )

    matches = manager.find_progress(
        job_type="download",
        statuses={"pending", "running", "canceling"},
        metadata={"record_id": "123", "file_key": "file-1"},
    )

    assert [match["job_id"] for match in matches] == [latest_id, first_id]


def test_progress_reporting_reader_checks_for_upload_cancellation():
    reader = ProgressReportingReader(
        BytesIO(b"content"),
        on_bytes_read=lambda size: None,
        should_cancel=lambda: True,
    )

    with pytest.raises(JobCancelled, match="Upload canceled"):
        reader.read()
