import React from 'react';

import { PickFilesButton } from './FilePicker';
import { JobProgress } from './JobProgress';
import { OpenRecordButton } from './OpenRecordButton';
import {
  useCurrentRemoteServer,
  useInvenioRDMRecordDraftUpload
} from '../core';
import { ErrorPanel } from './ErrorPanel';

/** Displays the workflow for creating a record draft from local files. */
export const InvenioRDMRecordDraftUpload: React.FC = () => {
  const {
    remoteServer,
    isLoading: isLoadingRemoteServer,
    error: remoteServerError
  } = useCurrentRemoteServer();
  const remoteName = remoteServer?.display_name;
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
  } = useInvenioRDMRecordDraftUpload(); // TODO maybe unify this with useInvenioRDMRecordFileUpload

  if (isLoadingRemoteServer) {
    return <p>Loading...</p>;
  }

  if (remoteServerError) {
    return <ErrorPanel error={remoteServerError} />;
  }

  if (!remoteName) {
    return <p>Remote server unavailable.</p>;
  }

  return (
    <div>
      <h2 className="m-0 text-sm font-semibold text-foreground">Upload</h2>
      <p>
        Upload files to a draft on {remoteName}. You will be able to edit the
        draft metadata and publish it on {remoteName} after the upload.
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
          <p>Created draft.</p>
          <OpenRecordButton record={result} text="Edit metadata" />
        </div>
      )}
    </div>
  );
};
