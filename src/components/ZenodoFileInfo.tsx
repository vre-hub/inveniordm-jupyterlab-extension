import React from 'react';

import {
  deleteZenodoRecordFile,
  downloadZenodoFile,
  getLatestActiveJobId,
  getZenodoFileImportCell
} from '../api_calls';
import { useInsertZenodoCell, useServerSettings } from '../store';
import { JobProgress } from './JobProgress';
import { ZenodoFileDownloadStatus } from './ZenodoFileDownloadStatus';
import type { ZenodoFile } from './ZenodoResource';

export const ZenodoFileInfo: React.FC<{
  file: ZenodoFile;
  recordId: string;
  editable: boolean;
}> = ({ file, recordId, editable }) => {
  const fileKey = file.key;

  return (
    <div
      style={{
        border: '1px solid #000000',
        padding: '3px',
        marginBottom: '2px'
      }}
    >
      <ZenodoFileDetails filename={fileKey} size={file.size} />
      <ZenodoFileDownload recordId={recordId} fileKey={fileKey} />
      <ZenodoFileImportCellButton recordId={recordId} fileKey={fileKey} />
      {editable && <ZenodoFileDeleteButton recordId={recordId} fileKey={fileKey} />}
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
  recordId: string;
  fileKey: string | null;
}> = ({ recordId, fileKey }) => {
  const serverSettings = useServerSettings();
  const [downloadId, setDownloadId] = React.useState<string | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const findDownload = async (): Promise<void> => {
      const jobId = fileKey
        ? await getLatestActiveJobId(serverSettings, {
            jobType: 'download',
            recordId,
            fileKey
          })
        : null;
      if (isMounted) {
        setDownloadId(jobId);
      }
    };

    void findDownload();
    return () => {
      isMounted = false;
    };
  }, [recordId, fileKey, serverSettings]);

  const download = async (): Promise<void> => {
    if (!fileKey) {
      return;
    }

    const response = await downloadZenodoFile(
      serverSettings,
      recordId,
      fileKey
    );
    setDownloadId(response.job_id);
  };

  return (
    <>
      <button disabled={!fileKey} onClick={download} type="button">
        Download in JupyterServer
      </button>
      {fileKey ? (
        <ZenodoFileDownloadStatus recordId={recordId} fileKey={fileKey} />
      ) : null}
      {downloadId ? <JobProgress jobId={downloadId} /> : null}
    </>
  );
};

const ZenodoFileImportCellButton: React.FC<{
  recordId: string;
  fileKey: string | null;
}> = ({ recordId, fileKey }) => {
  const serverSettings = useServerSettings();
  const insertZenodoCell = useInsertZenodoCell();

  const insertImportCell = async (): Promise<void> => {
    if (!fileKey) {
      return;
    }

    insertZenodoCell(
      await getZenodoFileImportCell(serverSettings, recordId, fileKey)
    );
  };

  return (
    <button disabled={!fileKey} onClick={insertImportCell} type="button">
      Insert import cell
    </button>
  );
};

const ZenodoFileDeleteButton: React.FC<{
  recordId: string;
  fileKey: string | null;
}> = ({ recordId, fileKey }) => {
  const serverSettings = useServerSettings();
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [isDeleted, setIsDeleted] = React.useState(false);

  const deleteFile = async (): Promise<void> => {
    if (!fileKey) {
      return;
    }

    setIsDeleting(true);
    try {
      await deleteZenodoRecordFile(serverSettings, recordId, fileKey);
      setIsDeleted(true);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      {isDeleted ? <div>Deleted from draft</div> : null}
      <button
        disabled={!fileKey || isDeleting || isDeleted}
        onClick={deleteFile}
        type="button"
      >
        {isDeleting ? 'Deleting…' : 'Delete from Zenodo'}
      </button>
    </>
  );
};
