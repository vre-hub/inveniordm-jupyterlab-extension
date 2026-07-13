import asyncio
from io import BytesIO
from threading import Event

import pytest

from zenodo_jupyterlab.util.job_manager import JobManager
from zenodo_jupyterlab.util.job_types import (
    DownloadProgress,
    JobCancelled,
    UploadProgress,
)
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
            bytes_uploaded=4,
            total_bytes=10,
            current_file="data.csv",
        )
        return {"deposition": {"id": 123}}

    upload_id = manager.start(
        upload,
        progress=UploadProgress(),
        on_progress_changed=lambda job_id, progress: progress_events.append(
            (job_id, progress)
        ),
    )

    progress = await wait_for_terminal_progress(manager, upload_id)
    await asyncio.sleep(0)

    assert progress == {
        "status": "done",
        "bytes_uploaded": 4,
        "total_bytes": 10,
        "current_file": "data.csv",
        "message": None,
        "deposition": {"id": 123},
        "cancel_requested": False,
    }
    assert progress_events[-1] == (upload_id, progress)


@pytest.mark.asyncio
async def test_download_job_keeps_its_own_progress_shape():
    manager = JobManager()

    def download(context):
        context.update(bytes_downloaded=5, total_bytes=None)
        return {"path": "/tmp/data.csv"}

    download_id = manager.start(download, progress=DownloadProgress())
    progress = await wait_for_terminal_progress(manager, download_id)

    assert progress == {
        "status": "done",
        "bytes_downloaded": 5,
        "total_bytes": None,
        "path": "/tmp/data.csv",
        "message": None,
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
        progress=UploadProgress(),
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
        return {"deposition": {"id": 123}}

    job_id = manager.start(job, progress=UploadProgress())
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

    job_id = manager.start(job, progress=DownloadProgress())
    progress = await wait_for_terminal_progress(manager, job_id)

    assert progress["status"] == "error"
    assert progress["message"] == "Could not transfer file"


def test_cancel_unknown_job_returns_none():
    assert JobManager().cancel("unknown") is None


def test_progress_reporting_reader_checks_for_upload_cancellation():
    reader = ProgressReportingReader(
        BytesIO(b"content"),
        on_bytes_read=lambda size: None,
        should_cancel=lambda: True,
    )

    with pytest.raises(JobCancelled, match="Upload canceled"):
        reader.read()
