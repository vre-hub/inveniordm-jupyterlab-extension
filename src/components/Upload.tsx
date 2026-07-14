import React from 'react';

import {
  MinimalRecordDraftResponse,
  createMinimalRecordDraft
} from '../api_calls';
import { useServerSettings } from '../store';
import { PickFilesButton } from './FilePicker';
import { JobProgress } from './JobProgress';

function getDraftUrl(record: MinimalRecordDraftResponse): string {
  return (
    record.links?.self_html ?? `https://sandbox.zenodo.org/uploads/${record.id}`
  );
}

export const Upload: React.FC = () => {
  const serverSettings = useServerSettings();
  const [filePaths, setFilePaths] = React.useState<string[]>([]);
  const [isCreatingDraft, setIsCreatingDraft] = React.useState(false);
  const [uploadId, setUploadId] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<MinimalRecordDraftResponse | null>(
    null
  );
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
      const upload = await createMinimalRecordDraft(serverSettings, filePaths);
      setUploadId(upload.job_id);
    } catch (reason) {
      setError(String(reason));
      setIsCreatingDraft(false);
    }
  };

  const completeUpload = React.useCallback(
    (record: MinimalRecordDraftResponse): void => {
      setResult(record);
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
        <JobProgress
          onCanceled={cancelUploadJob}
          onDone={progress => {
            const draft = progress.result?.draft;
            if (draft) {
              completeUpload(draft);
            } else {
              failUpload('Upload completed without a record');
            }
          }}
          onError={failUpload}
          jobId={uploadId}
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
