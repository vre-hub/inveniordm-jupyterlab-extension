import React from 'react';

import { JobProgress } from './JobProgress';
import type { ZenodoFile } from '../api_calls';
import {
  useDeleteDownload,
  useDeleteZenodoFile,
  useDownloadStatus,
  useDownloadZenodoFile,
  useInsertImportCell,
  useZenodoFileIdentifierFromProps
} from '../core';

export const ZenodoFileInfo: React.FC<{
  file: ZenodoFile;
  recordId: string;
  isDraft: boolean;
  editable: boolean;
}> = ({ file, recordId, isDraft, editable }) => {
  const fileId = useZenodoFileIdentifierFromProps(file, recordId, isDraft);
  const { status } = useDownloadStatus(fileId);
  const { deleteDownload } = useDeleteDownload(fileId);
  const { insertImportCell } = useInsertImportCell(fileId);
  const { deleteFile, isDeleting } = useDeleteZenodoFile(fileId);

  const { download, downloadId } = useDownloadZenodoFile(fileId); // TODO how to split this so that both the download button and the status can use it with correct download id

  if (status === null) {
    return <div>Checking download status...</div>;
  }

  return (
    <div
      style={{
        border: '1px solid #000000',
        padding: '3px',
        marginBottom: '2px'
      }}
    >
      <div>
        {file.key}
        {/* TODO display file size in a reasonable unit */}
        {file.size ? ` (${(file.size / 1024 / 1024).toFixed(2)} MB)` : null}
      </div>
      <div>
        {status.downloaded ? '✅ Downloaded' : '❌ Not downloaded'}
        {downloadId ? <JobProgress jobId={downloadId} /> : null}
      </div>
      <br />
      Actions:
      <br />
      <button
        disabled={status.downloaded !== false}
        onClick={download}
        title={status.downloaded ? 'File is already downloaded.' : undefined}
        type="button"
      >
        Download in JupyterServer
      </button>
      {status.downloaded && (
        <React.Fragment>
          <button onClick={deleteDownload} type="button">
            Delete download
          </button>
          <button onClick={insertImportCell} type="button">
            Insert import cell
          </button>
        </React.Fragment>
      )}
      <button disabled={isDeleting} onClick={deleteFile} type="button">
        {isDeleting ? 'Deleting…' : 'Delete from Zenodo'}
      </button>
    </div>
  );
};
