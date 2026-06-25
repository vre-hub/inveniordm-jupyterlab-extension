import React from 'react';

import {
  cancelDownload,
  useDownloadProgress,
} from '../api_calls';
import { useServerSettings } from '../store';

export const ZenodoDownloadProgress: React.FC<{
  downloadId: string;
}> = ({ downloadId }) => {
  const serverSettings = useServerSettings();
  const progress = useDownloadProgress(downloadId);

  const cancel = async (): Promise<void> => {
    await cancelDownload(serverSettings, downloadId)
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
