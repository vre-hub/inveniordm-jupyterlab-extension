import React from 'react';

import {
  getLatestActiveJobId,
  uploadZenodoRecordFiles
} from '../api_calls';
import { useServerSettings } from '../store';
import { PickFilesButton } from './FilePicker';
import { JobProgress } from './JobProgress';

export const ZenodoRecordFileUpload: React.FC<{
  recordId: string;
  onDone: () => void;
}> = ({ recordId, onDone }) => {
  const serverSettings = useServerSettings();
  const [uploadId, setUploadId] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [message, setMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const findUpload = async (): Promise<void> => {
      const jobId = await getLatestActiveJobId(serverSettings, {
        jobType: 'upload',
        recordId
      });
      if (isMounted) {
        setUploadId(jobId);
      }
    };

    void findUpload();
    return () => {
      isMounted = false;
    };
  }, [recordId, serverSettings]);

  const uploadFiles = async (filePaths: string[]): Promise<void> => {
    setError(null);
    setMessage(null);

    try {
      const upload = await uploadZenodoRecordFiles(
        serverSettings,
        recordId,
        filePaths
      );
      setUploadId(upload.job_id);
    } catch (reason) {
      setError(String(reason));
    }
  };

  const completeUpload = React.useCallback((): void => {
    setUploadId(null);
    setMessage('Files uploaded.');
    onDone();
  }, [onDone]);

  const failUpload = React.useCallback((reason: string): void => {
    setUploadId(null);
    setError(reason);
  }, []);

  const cancelUpload = React.useCallback((reason: string): void => {
    setUploadId(null);
    setMessage(reason);
  }, []);

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
