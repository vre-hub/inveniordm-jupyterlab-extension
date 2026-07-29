import React from 'react';

import {
  deleteZenodoRecordFile,
  downloadZenodoFile,
  getLatestActiveJobId
} from '../api_calls';
import { useServerSettings } from '../store';
import { JobProgress } from './JobProgress';
import { ZenodoFileDownloadStatus } from './ZenodoFileDownloadStatus';
import type { ZenodoFile, ZenodoFileIdentifier } from '../api_calls';

export const ZenodoFileInfo: React.FC<{
  file: ZenodoFile;
  recordId: string;
  isDraft: boolean;
  editable: boolean;
}> = ({ file, recordId, isDraft, editable }) => {
  const fileKey = file.key;

  const fileId = React.useMemo<ZenodoFileIdentifier>(
    () => ({
      file_key: fileKey,
      record_id: recordId,
      record_status: isDraft ? 'draft' : 'published'
    }),
    [fileKey, isDraft, recordId]
  );

  return (
    <div
      style={{
        border: '1px solid #000000',
        padding: '3px',
        marginBottom: '2px'
      }}
    >
      <ZenodoFileDetails filename={fileKey} size={file.size} />
      <ZenodoFileDownload fileId={fileId} />
      {editable && <ZenodoFileDeleteButton fileId={fileId} />}
    </div>
  );
};

const ZenodoFileDetails: React.FC<{
  filename: string;
  size?: number;
}> = ({ filename, size }) => (
  <div>
    {filename}
    {/* TODO display file size in a reasonable unit */}
    {size ? ` (${(size / 1024 / 1024).toFixed(2)} MB)` : null}
  </div>
);

const ZenodoFileDownload: React.FC<{
  fileId: ZenodoFileIdentifier;
}> = ({ fileId }) => {
  const serverSettings = useServerSettings();
  const [downloadId, setDownloadId] = React.useState<string | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const findDownload = async (): Promise<void> => {
      const jobId = await getLatestActiveJobId(serverSettings, {
        jobType: 'download',
        fileId
      });
      if (isMounted) {
        setDownloadId(jobId);
      }
    };

    void findDownload();
    return () => {
      isMounted = false;
    };
  }, [fileId, serverSettings]);

  const download = async (): Promise<void> => {
    const response = await downloadZenodoFile(serverSettings, fileId);
    setDownloadId(response.job_id);
  };

  return (
    <>
      <button onClick={download} type="button">
        Download in JupyterServer
      </button>
      <ZenodoFileDownloadStatus fileId={fileId} />
      {downloadId ? <JobProgress jobId={downloadId} /> : null}
    </>
  );
};

const ZenodoFileDeleteButton: React.FC<{
  fileId: ZenodoFileIdentifier;
}> = ({ fileId }) => {
  const serverSettings = useServerSettings();
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [isDeleted, setIsDeleted] = React.useState(false);

  const deleteFile = async (): Promise<void> => {
    setIsDeleting(true);
    try {
      await deleteZenodoRecordFile(serverSettings, fileId);
      setIsDeleted(true);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      {isDeleted ? <div>Deleted from draft</div> : null}
      <button
        disabled={isDeleting || isDeleted}
        onClick={deleteFile}
        type="button"
      >
        {isDeleting ? 'Deleting…' : 'Delete from Zenodo'}
      </button>
    </>
  );
};
