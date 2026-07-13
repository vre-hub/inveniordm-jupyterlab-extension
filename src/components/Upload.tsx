import React from 'react';

import {
  MinimalDepositionDraftResponse,
  UploadProgressResponse,
  cancelUpload,
  createMinimalDepositionDraft,
  getUploadProgress,
  useUploadProgress
} from '../api_calls';
import { useServerSettings } from '../store';
import { PickFilesButton } from './FilePicker';

function getDraftUrl(deposition: MinimalDepositionDraftResponse): string {
  return (
    deposition.links?.latest_draft_html ??
    `https://sandbox.zenodo.org/uploads/${deposition.id}`
  );
}

const UploadProgress: React.FC<{
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

export const Upload: React.FC = () => {
  const serverSettings = useServerSettings();
  const [filePaths, setFilePaths] = React.useState<string[]>([]);
  const [isCreatingDraft, setIsCreatingDraft] = React.useState(false);
  const [uploadId, setUploadId] = React.useState<string | null>(null);
  const [result, setResult] =
    React.useState<MinimalDepositionDraftResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [message, setMessage] = React.useState<string | null>(null);
  const canCreateDraft = filePaths.length > 0 && !isCreatingDraft;

  const onSubmit = async (event: React.FormEvent): Promise<void> => {
    event.preventDefault();
    if (!canCreateDraft) {
      return;
    }

    setIsCreatingDraft(true);
    setUploadId(null);
    setResult(null);
    setError(null);
    setMessage(null);

    try {
      const upload = await createMinimalDepositionDraft(
        serverSettings,
        filePaths
      );
      setUploadId(upload.upload_id);
    } catch (reason) {
      setError(String(reason));
      setIsCreatingDraft(false);
    }
  };

  const completeUpload = React.useCallback(
    (deposition: MinimalDepositionDraftResponse): void => {
      setResult(deposition);
      setIsCreatingDraft(false);
      setUploadId(null);
    },
    []
  );

  const failUpload = React.useCallback((message: string): void => {
    setError(message);
    setIsCreatingDraft(false);
    setUploadId(null);
  }, []);

  const cancelUploadJob = React.useCallback((message: string): void => {
    setMessage(message);
    setIsCreatingDraft(false);
    setUploadId(null);
  }, []);

  return (
    <form onSubmit={onSubmit}>
      <h2>Upload</h2>
      <p>
        Upload files to a Zenodo draft. You will be able to edit the draft
        metadata and publish it on Zenodo after the upload.
      </p>
      <PickFilesButton
        buttonText="Select files"
        onFilesSelected={files => setFilePaths(files)}
      />
      {filePaths.length > 0 && (
        <ul>
          {filePaths.map(filePath => (
            <li key={filePath}>{filePath}</li>
          ))}
        </ul>
      )}
      <button disabled={!canCreateDraft} type="submit">
        {isCreatingDraft ? 'Uploading files...' : 'Upload to Zenodo Draft'}
      </button>
      {uploadId ? (
        <UploadProgress
          onCanceled={cancelUploadJob}
          onDone={completeUpload}
          onError={failUpload}
          uploadId={uploadId}
        />
      ) : null}
      {error && <p>{error}</p>}
      {message && <p>{message}</p>}
      {result && (
        <div>
          <p>Created draft {result.id}.</p>
          <button
            onClick={() => window.open(getDraftUrl(result), '_blank')}
            type="button"
          >
            Open draft
          </button>
        </div>
      )}
    </form>
  );
};
