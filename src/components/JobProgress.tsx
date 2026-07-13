import React from 'react';

import {
  JobProgressResponse,
  cancelJob,
  getJobProgress,
  useJobProgress
} from '../api_calls';
import { useServerSettings } from '../store';

const TERMINAL_STATUSES = new Set(['done', 'error', 'canceled']);

export const JobProgress: React.FC<{
  jobId: string;
  onDone?: (progress: JobProgressResponse) => void;
  onCanceled?: (message: string) => void;
  onError?: (message: string) => void;
}> = ({ jobId, onDone, onCanceled, onError }) => {
  const serverSettings = useServerSettings();
  const eventProgress = useJobProgress(jobId);
  const [progress, setProgress] = React.useState<JobProgressResponse | null>(
    null
  );
  const hasHandledTerminalStatus = React.useRef(false);

  React.useEffect(() => {
    let isMounted = true;
    let timeout: number | undefined;

    setProgress(null);
    hasHandledTerminalStatus.current = false;

    const loadProgress = async (): Promise<void> => {
      try {
        const latestProgress = await getJobProgress(serverSettings, jobId);
        if (isMounted) {
          setProgress(latestProgress);
          if (!TERMINAL_STATUSES.has(latestProgress.status)) {
            timeout = window.setTimeout(loadProgress, 1000);
          }
        }
      } catch (reason) {
        if (isMounted) {
          onError?.(String(reason));
        }
      }
    };

    void loadProgress();

    return () => {
      isMounted = false;
      if (timeout !== undefined) {
        window.clearTimeout(timeout);
      }
    };
  }, [jobId, onError, serverSettings]);

  React.useEffect(() => {
    if (eventProgress?.job_id === jobId) {
      setProgress(eventProgress);
    }
  }, [eventProgress, jobId]);

  React.useEffect(() => {
    if (
      !progress ||
      progress.job_id !== jobId ||
      hasHandledTerminalStatus.current
    ) {
      return;
    }

    if (progress.status === 'error') {
      hasHandledTerminalStatus.current = true;
      onError?.(progress.message ?? 'Job failed');
      return;
    }

    if (progress.status === 'canceled') {
      hasHandledTerminalStatus.current = true;
      onCanceled?.(progress.message ?? 'Job canceled');
      return;
    }

    if (progress.status === 'done') {
      hasHandledTerminalStatus.current = true;
      onDone?.(progress);
    }
  }, [jobId, onCanceled, onDone, onError, progress]);

  if (!progress || progress.job_id !== jobId) {
    return <p>Loading...</p>;
  }

  const progressLabel =
    progress.total_bytes !== null && progress.total_bytes > 0
      ? `${Math.round(
          (progress.completed_bytes / progress.total_bytes) * 100
        )}%`
      : `${progress.completed_bytes} bytes`;
  const canCancel =
    progress.status === 'pending' || progress.status === 'running';

  const cancel = async (): Promise<void> => {
    try {
      setProgress(await cancelJob(serverSettings, jobId));
    } catch (reason) {
      onError?.(String(reason));
    }
  };

  return (
    <div>
      {canCancel ? (
        <button onClick={cancel} type="button">
          Cancel job
        </button>
      ) : null}
      <progress
        value={progress.completed_bytes}
        max={progress.total_bytes ?? undefined}
      />
      <span>
        {progress.status} {progressLabel}
        {progress.current_item ? ` - ${progress.current_item}` : ''}
      </span>
      {progress.message ? <div>{progress.message}</div> : null}
    </div>
  );
};
