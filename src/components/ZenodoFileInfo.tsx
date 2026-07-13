import React from 'react';

import { downloadZenodoFile, getZenodoFileImportCell } from '../api_calls';
import { useInsertZenodoCell, useServerSettings } from '../store';
import { JobProgress } from './JobProgress';
import { ZenodoFileDownloadStatus } from './ZenodoFileDownloadStatus';
import type { ZenodoFile } from './ZenodoResource';

export const ZenodoFileInfo: React.FC<{
  file: ZenodoFile;
  depositionId: number;
}> = ({ file, depositionId }) => {
  const serverSettings = useServerSettings();
  const insertZenodoCell = useInsertZenodoCell();
  const [downloadId, setDownloadId] = React.useState<string | null>(null);
  const filename = file.key ?? file.filename ?? file.id ?? 'download';
  const fileId = file.file_id ?? file.id ?? null;

  const download = async (): Promise<void> => {
    const response = await downloadZenodoFile(
      serverSettings,
      depositionId,
      fileId
    );
    setDownloadId(response.job_id);
  };
  const insertImportCell = async (): Promise<void> => {
    insertZenodoCell(
      await getZenodoFileImportCell(serverSettings, depositionId, fileId)
    );
  };

  return (
    <div
      style={{
        border: '1px solid #000000',
        padding: '3px',
        marginBottom: '2px'
      }}
    >
      <div>
        {filename}
        {/* TODO display file size in a reasonable unit */}
        {file.size ? ` (${(file.size / 1024 / 1024).toFixed(2)} MB)` : null}
      </div>
      <button disabled={!fileId} onClick={download} type="button">
        Download in JupyterServer
      </button>
      <button disabled={!fileId} onClick={insertImportCell} type="button">
        Insert import cell
      </button>
      {fileId ? (
        <ZenodoFileDownloadStatus depositionId={depositionId} fileId={fileId} />
      ) : null}
      {downloadId ? <JobProgress jobId={downloadId} /> : null}
    </div>
  );
};
