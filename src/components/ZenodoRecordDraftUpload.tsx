import React from 'react';

import { PickFilesButton } from './FilePicker';
import { JobProgress } from './JobProgress';
import { OpenRecordButton } from './OpenRecordButton';
import { useZenodoRecordDraftUpload } from '../core/useZenodoRecordDraftUpload';

export const ZenodoRecordDraftUpload: React.FC = () => {
  const {
    isCreatingDraft,
    uploadId,
    result,
    error,
    message,
    uploadFiles,
    completeUpload,
    failUpload,
    cancelUploadJob
  } = useZenodoRecordDraftUpload(); // TODO maybe unify this with useZenodoRecordFileUpload

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
