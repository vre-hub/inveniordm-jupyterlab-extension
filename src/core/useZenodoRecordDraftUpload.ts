import React from 'react';
import {
  ZenodoRecordDraftResponse,
  createZenodoRecordDraftWithFiles
} from '../api_calls';
import { useServerSettings } from '../store';

export function useZenodoRecordDraftUpload() {
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

  return {
    isCreatingDraft,
    uploadId,
    result,
    error,
    message,
    uploadFiles,
    completeUpload,
    failUpload,
    cancelUploadJob
  };
}
