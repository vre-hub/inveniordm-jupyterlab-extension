import React from 'react';

import {
  MinimalDepositionDraftResponse,
  UploadProgressResponse,
  cancelUpload,
  getUploadProgress,
  useUploadProgress
} from '../api_calls';
import { useServerSettings } from '../store';

export const UploadProgress: React.FC<{
  onDone: (deposition: MinimalDepositionDraftResponse) => void;
  onCanceled: (message: string) => void;
  onError: (message: string) => void;
  uploadId: string;
}> = ({ onDone, onCanceled, onError, uploadId }) => {
  const serverSettings = useServerSettings();
  const eventProgress = useUploadProgress(uploadId);
  const [progress, setProgress] = React.useState<UploadProgressResponse | null>(
    null
  );
  const hasHandledTerminalStatus = React.useRef(false);

  React.useEffect(() => {
    let isMounted = true;
    let timeout: number | undefined;

    const loadProgress = async (): Promise<void> => {
      try {
        const latestProgress = await getUploadProgress(
          serverSettings,
          uploadId
        );
        if (isMounted) {
          setProgress(latestProgress);
          if (
            latestProgress.status !== 'done' &&
            latestProgress.status !== 'error' &&
            latestProgress.status !== 'canceled'
          ) {
            timeout = window.setTimeout(loadProgress, 1000);
          }
        }
      } catch (reason) {
        if (isMounted) {
          onError(String(reason));
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
  }, [onError, serverSettings, uploadId]);

  React.useEffect(() => {
    if (eventProgress) {
      setProgress(eventProgress);
    }
  }, [eventProgress]);

  React.useEffect(() => {
    if (!progress || hasHandledTerminalStatus.current) {
      return;
    }

    if (progress.status === 'error') {
      hasHandledTerminalStatus.current = true;
      onError(progress.message ?? 'Upload failed');
      return;
    }

    if (progress.status === 'canceled') {
      hasHandledTerminalStatus.current = true;
      onCanceled(progress.message ?? 'Upload canceled');
      return;
    }

    if (progress.status === 'done' && progress.deposition) {
      hasHandledTerminalStatus.current = true;
      onDone(progress.deposition);
    }
  }, [onCanceled, onDone, onError, progress]);

  if (!progress) {
    return <p>Starting upload...</p>;
  }

  const progressLabel =
    progress.total_bytes > 0
      ? `${Math.round((progress.bytes_uploaded / progress.total_bytes) * 100)}%`
      : `${progress.bytes_uploaded} bytes`;
  const canCancel =
    progress.status === 'pending' || progress.status === 'running';

  const cancel = async (): Promise<void> => {
    try {
      const cancelProgress = await cancelUpload(serverSettings, uploadId);
      setProgress(cancelProgress);
    } catch (reason) {
      onError(String(reason));
    }
  };

  return (
    <div>
      {canCancel ? (
        <button onClick={cancel} type="button">
          Cancel upload
        </button>
      ) : null}
      <progress
        value={progress.bytes_uploaded}
        max={progress.total_bytes || undefined}
      />
      <span>
        {progress.status} {progressLabel}
        {progress.current_file ? ` - ${progress.current_file}` : ''}
      </span>
      {progress.message ? <div>{progress.message}</div> : null}
    </div>
  );
};
