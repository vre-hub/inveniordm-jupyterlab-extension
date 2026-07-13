import React from 'react';

import {
  deleteZenodoDepositionFile,
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
  depositionId: number;
}> = ({ file, depositionId }) => {
  const filename = file.key ?? file.filename ?? file.id ?? 'download';
  const fileKey = file.key ?? file.filename ?? null;
  const fileId = file.file_id ?? file.id ?? null;

  return (
    <div
      style={{
        border: '1px solid #000000',
        padding: '3px',
        marginBottom: '2px'
      }}
    >
      <ZenodoFileDetails filename={filename} size={file.size} />
      <ZenodoFileDownload depositionId={depositionId} fileId={fileId} />
      <ZenodoFileImportCellButton depositionId={depositionId} fileId={fileId} />
      <ZenodoFileDeleteButton depositionId={depositionId} fileKey={fileKey} />
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
  depositionId: number;
  fileId: string | null;
}> = ({ depositionId, fileId }) => {
  const serverSettings = useServerSettings();
  const [downloadId, setDownloadId] = React.useState<string | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const findDownload = async (): Promise<void> => {
      const jobId = fileId
        ? await getLatestActiveJobId(serverSettings, {
            jobType: 'download',
            depositionId,
            fileId
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
  }, [depositionId, fileId, serverSettings]);

  const download = async (): Promise<void> => {
    if (!fileId) {
      return;
    }

    const response = await downloadZenodoFile(
      serverSettings,
      depositionId,
      fileId
    );
    setDownloadId(response.job_id);
  };

  return (
    <>
      <button disabled={!fileId} onClick={download} type="button">
        Download in JupyterServer
      </button>
      {fileId ? (
        <ZenodoFileDownloadStatus depositionId={depositionId} fileId={fileId} />
      ) : null}
      {downloadId ? <JobProgress jobId={downloadId} /> : null}
    </>
  );
};

const ZenodoFileImportCellButton: React.FC<{
  depositionId: number;
  fileId: string | null;
}> = ({ depositionId, fileId }) => {
  const serverSettings = useServerSettings();
  const insertZenodoCell = useInsertZenodoCell();

  const insertImportCell = async (): Promise<void> => {
    if (!fileId) {
      return;
    }

    insertZenodoCell(
      await getZenodoFileImportCell(serverSettings, depositionId, fileId)
    );
  };

  return (
    <button disabled={!fileId} onClick={insertImportCell} type="button">
      Insert import cell
    </button>
  );
};

const ZenodoFileDeleteButton: React.FC<{
  depositionId: number;
  fileKey: string | null;
}> = ({ depositionId, fileKey }) => {
  const serverSettings = useServerSettings();
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [isDeleted, setIsDeleted] = React.useState(false);

  const deleteFile = async (): Promise<void> => {
    if (!fileKey) {
      return;
    }

    setIsDeleting(true);
    try {
      await deleteZenodoDepositionFile(serverSettings, depositionId, fileKey);
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
