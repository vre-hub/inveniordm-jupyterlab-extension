from collections.abc import Mapping
from dataclasses import asdict
from threading import Lock
from typing import Callable
from uuid import uuid4

import tornado.ioloop

from .job_types import JobCancelled, JobProgress

ProgressListener = Callable[[str, dict[str, object]], None]
JobCallable = Callable[["JobContext"], Mapping[str, object]]

_TERMINAL_STATUSES = {"done", "error", "canceled"}


class JobProgressStore:
    """Store thread-safe progress snapshots for background jobs."""
    def __init__(self):
        """Initialize an empty, lock-protected progress store."""
        self._progress: dict[str, JobProgress] = {}
        self._lock = Lock()

    def create(self, progress: JobProgress) -> str:
        """Assign an identifier and store a new progress record."""
        job_id = uuid4().hex
        progress.job_id = job_id
        with self._lock:
            self._progress[job_id] = progress
        return job_id

    def update(self, job_id: str, **changes: object) -> None:
        """Apply field changes to a progress record atomically."""
        with self._lock:
            progress = self._progress[job_id]
            for key, value in changes.items():
                setattr(progress, key, value)

    def request_cancel(self, job_id: str) -> dict[str, object] | None:
        """Mark a nonterminal job for cooperative cancellation."""
        with self._lock:
            progress = self._progress.get(job_id)
            if progress is None:
                return None
            if progress.status in _TERMINAL_STATUSES:
                return asdict(progress)

            progress.cancel_requested = True
            progress.status = "canceling"
            return asdict(progress)

    def cancel_requested(self, job_id: str) -> bool:
        """Return whether cancellation was requested for a job."""
        with self._lock:
            progress = self._progress.get(job_id)
            return bool(progress and progress.cancel_requested)

    def get(self, job_id: str) -> dict[str, object] | None:
        """Return an isolated progress snapshot for a job."""
        with self._lock:
            progress = self._progress.get(job_id)
            return asdict(progress) if progress is not None else None

    def find(
        self,
        *,
        job_type: str | None = None,
        statuses: set[str] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> list[dict[str, object]]:
        """Find newest-first jobs matching all supplied filters."""
        with self._lock:
            matches = []
            for progress in reversed(self._progress.values()):
                if job_type is not None and progress.job_type != job_type:
                    continue
                if statuses is not None and progress.status not in statuses:
                    continue
                if metadata is not None and any(
                    progress.metadata.get(key) != value
                    for key, value in metadata.items()
                ):
                    continue
                matches.append(asdict(progress))
            return matches


class JobContext:
    """Expose progress updates and cancellation checks to a running job."""
    def __init__(
        self,
        job_id: str,
        progress_store: JobProgressStore,
        notify_progress_changed: Callable[[], None],
    ):
        """Bind a running job to its store and notification callback."""
        self.job_id = job_id
        self._progress_store = progress_store
        self._notify_progress_changed = notify_progress_changed

    def update(self, **changes: object) -> None:
        """Update progress and notify listeners."""
        self._progress_store.update(self.job_id, **changes)
        self._notify_progress_changed()

    def should_cancel(self) -> bool:
        """Return whether the job should stop cooperatively."""
        return self._progress_store.cancel_requested(self.job_id)


class JobManager:
    """Run background jobs and track their progress and cancellation."""

    def __init__(self):
        """Initialize job state associated with the current process."""
        self.progress_store = JobProgressStore()
        self._progress_listeners: dict[str, ProgressListener] = {}
        self._io_loops: dict[str, tornado.ioloop.IOLoop] = {}

    def start(
        self,
        job: JobCallable,
        *,
        progress: JobProgress,
        on_progress_changed: ProgressListener | None = None,
        cancel_message: str = "Job canceled",
    ) -> str:
        """Schedule a synchronous job without blocking Tornado's event loop.

        The callable runs in an executor and receives a context for cooperative
        cancellation and progress updates. Completion, cancellation, and errors
        become terminal progress states before listeners are removed.
        """
        job_id = self.progress_store.create(progress)
        io_loop = tornado.ioloop.IOLoop.current()
        if on_progress_changed is not None:
            self._progress_listeners[job_id] = on_progress_changed
        self._io_loops[job_id] = io_loop

        def notify_progress_changed() -> None:
            """Schedule notification of the current progress snapshot."""
            self._notify_progress_changed(
                job_id,
                io_loop,
                on_progress_changed,
            )

        context = JobContext(
            job_id,
            self.progress_store,
            notify_progress_changed,
        )

        async def run_job() -> None:
            """Run the job and translate its outcome into progress state."""
            try:
                if context.should_cancel():
                    context.update(status="canceled", message=cancel_message)
                    return

                context.update(status="running")
                try:
                    result = await io_loop.run_in_executor(
                        None,
                        lambda: job(context),
                    )
                except JobCancelled as error:
                    context.update(
                        status="canceled",
                        message=str(error) or cancel_message,
                    )
                    return
                except Exception as error:
                    context.update(status="error", message=str(error))
                    return

                context.update(status="done", result=dict(result))
            finally:
                self._progress_listeners.pop(job_id, None)
                self._io_loops.pop(job_id, None)

        io_loop.spawn_callback(run_job)
        return job_id

    def get_progress(self, job_id: str) -> dict[str, object] | None:
        """Return the latest progress snapshot for a job."""
        return self.progress_store.get(job_id)

    def find_progress(
        self,
        *,
        job_type: str | None = None,
        statuses: set[str] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> list[dict[str, object]]:
        """Find progress snapshots matching all supplied filters."""
        return self.progress_store.find(
            job_type=job_type,
            statuses=statuses,
            metadata=metadata,
        )

    def cancel(self, job_id: str) -> dict[str, object] | None:
        """Request cancellation and immediately notify any listener."""
        progress = self.progress_store.request_cancel(job_id)
        io_loop = self._io_loops.get(job_id)
        on_progress_changed = self._progress_listeners.get(job_id)
        if (
            progress is not None
            and io_loop is not None
            and on_progress_changed is not None
        ):
            self._notify_progress_changed(
                job_id,
                io_loop,
                on_progress_changed,
                progress=progress,
            )
        return progress

    def _notify_progress_changed(
        self,
        job_id: str,
        io_loop: tornado.ioloop.IOLoop,
        on_progress_changed: ProgressListener | None,
        *,
        progress: dict[str, object] | None = None,
    ) -> None:
        """Dispatch a progress snapshot on the originating I/O loop."""
        if on_progress_changed is None:
            return

        progress = progress or self.progress_store.get(job_id)
        if progress is None:
            return

        io_loop.add_callback(on_progress_changed, job_id, progress)
