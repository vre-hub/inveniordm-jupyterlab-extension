import React from 'react';

import {
  cancelDownload,
  DownloadProgressResponse,
  getDownloadProgress
} from '../api_calls';
import { useServerSettings } from '../store';

export const ZenodoDownloadProgress: React.FC<{
  downloadId: string;
}> = ({ downloadId }) => {
  const serverSettings = useServerSettings();
  const [progress, setProgress] =
    React.useState<DownloadProgressResponse | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const poll = async (): Promise<void> => {
      const nextProgress = await getDownloadProgress(serverSettings, downloadId);
      if (!isMounted) {
        return;
      }
      setProgress(nextProgress);
      if (
        nextProgress.status === 'done' ||
        nextProgress.status === 'canceled' ||
        nextProgress.status === 'error'
      ) {
        window.clearInterval(interval);
      }
    };

    setProgress({
      status: 'pending',
      bytes_downloaded: 0,
      total_bytes: null,
      path: null,
      message: null,
      cancel_requested: false
    });
    const interval = window.setInterval(poll, 500);
    poll();

    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, [downloadId, serverSettings]);

  const cancel = async (): Promise<void> => {
    setProgress(await cancelDownload(serverSettings, downloadId));
  };
  const progressLabel =
    progress?.total_bytes && progress.total_bytes > 0
      ? `${Math.round((progress.bytes_downloaded / progress.total_bytes) * 100)}%`
      : progress
        ? `${progress.bytes_downloaded} bytes`
        : null;
  const canCancel =
    progress !== null &&
    (progress.status === 'pending' || progress.status === 'running');

  if (progress === null) {
    return null;
  }

  return (
    <div>
      {canCancel ? (
        <button onClick={cancel} type="button">
          Cancel download
        </button>
      ) : null}
      <progress
        value={progress.bytes_downloaded}
        max={progress.total_bytes ?? undefined}
      />
      <span>
        {progress.status} {progressLabel}
      </span>
      {progress.message ? <div>{progress.message}</div> : null}
    </div>
  );
};
