import React from 'react';

import {
  MinimalDepositionDraftResponse,
  uploadFilesToDeposition
} from '../api_calls';
import { useServerSettings } from '../store';
import { PickFilesButton } from './FilePicker';
import { UploadProgress } from './UploadProgress';

export const DepositionUpload: React.FC<{
  depositionId: number;
  onDone: () => void;
}> = ({ depositionId, onDone }) => {
  const serverSettings = useServerSettings();
  const [uploadId, setUploadId] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [message, setMessage] = React.useState<string | null>(null);

  const uploadFiles = async (filePaths: string[]): Promise<void> => {
    setError(null);
    setMessage(null);

    try {
      const upload = await uploadFilesToDeposition(
        serverSettings,
        depositionId,
        filePaths
      );
      setUploadId(upload.upload_id);
    } catch (reason) {
      setError(String(reason));
    }
  };

  const completeUpload = React.useCallback(
    (_deposition: MinimalDepositionDraftResponse): void => {
      setUploadId(null);
      setMessage('Files uploaded.');
      onDone();
    },
    [onDone]
  );

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
        <UploadProgress
          onCanceled={cancelUpload}
          onDone={completeUpload}
          onError={failUpload}
          uploadId={uploadId}
        />
      ) : null}
      {error ? <p>{error}</p> : null}
      {message ? <p>{message}</p> : null}
    </div>
  );
};
