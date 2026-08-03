import React from 'react';

import { PickFilesButton } from './FilePicker';
import { JobProgress } from './JobProgress';
import { useZenodoRecordFileUpload } from '../core/useZenodoRecordFileUpload';

export const ZenodoRecordFileUpload: React.FC<{
  recordId: string;
}> = ({ recordId }) => {
  const {
    uploadId,
    error,
    message,
    uploadFiles,
    completeUpload,
    failUpload,
    cancelUpload
  } = useZenodoRecordFileUpload(recordId);

  return (
    <div>
      {!uploadId ? (
        <PickFilesButton
          buttonText="Upload files"
          onFilesSelected={files => void uploadFiles(files)}
        />
      ) : null}
      {uploadId ? (
        <JobProgress
          onCanceled={cancelUpload}
          onDone={completeUpload}
          onError={failUpload}
          jobId={uploadId}
        />
      ) : null}
      {error ? <p>{error}</p> : null}
      {message ? <p>{message}</p> : null}
    </div>
  );
};
