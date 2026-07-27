import React from 'react';

import {
  ZenodoRecordDraftResponse,
  createZenodoRecordDraftWithFiles
} from '../api_calls';
import { useServerSettings } from '../store';
import { PickFilesButton } from './FilePicker';
import { JobProgress } from './JobProgress';
import { OpenRecordButton } from './OpenRecordButton';

export const ZenodoRecordDraftUpload: React.FC = () => {
  const serverSettings = useServerSettings();
  const [isCreatingDraft, setIsCreatingDraft] = React.useState(false);
  const [uploadId, setUploadId] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<ZenodoRecordDraftResponse | null>(
    null
  );
  const [error, setError] = React.useState<string | null>(null);
  const [message, setMessage] = React.useState<string | null>(null);

  const uploadFiles = async (filePaths: string[]): Promise<void> => {
    if (filePaths.length === 0 || isCreatingDraft) {
      return;
    }

    setIsCreatingDraft(true);
    setUploadId(null);
    setResult(null);
    setError(null);
    setMessage(null);

    try {
      const upload = await createZenodoRecordDraftWithFiles(
        serverSettings,
        filePaths
      );
      setUploadId(upload.job_id);
    } catch (reason) {
      setError(String(reason));
      setIsCreatingDraft(false);
    }
  };

  const completeUpload = React.useCallback(
    (record: ZenodoRecordDraftResponse): void => {
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
    <div>
      <h2>Upload</h2>
      <p>
        Upload files to a Zenodo draft. You will be able to edit the draft
        metadata and publish it on Zenodo after the upload.
      </p>
      <PickFilesButton
        buttonText={isCreatingDraft ? 'Uploading files...' : 'Select files'}
        disabled={isCreatingDraft}
        onFilesSelected={files => void uploadFiles(files)}
      />
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
          <OpenRecordButton record={result} text="Edit metadata" />
        </div>
      )}
    </div>
  );
};
