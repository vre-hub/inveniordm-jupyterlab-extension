import React from 'react';
import { Download } from 'lucide-react';

import { JobProgress } from './JobProgress';
import { InvenioRDMFileActions } from './InvenioRDMFileActions';
import type { InvenioRDMFile } from '../api_calls';
import {
  useDownloadStatus,
  useDownloadInvenioRDMFile,
  useInvenioRDMFileIdentifierFromProps
} from '../core';

/** Displays file metadata and the actions available for the file. */
export const InvenioRDMFileInfo: React.FC<{
  file: InvenioRDMFile;
  recordId: string;
  isDraft: boolean;
  editable: boolean;
}> = ({ file, recordId, isDraft, editable }) => {
  const fileId = useInvenioRDMFileIdentifierFromProps(file, recordId, isDraft);
  const { status } = useDownloadStatus(fileId);

  const { download, downloadId } = useDownloadInvenioRDMFile(fileId); // TODO both the download button and the status need this, fix if we want to split this into separate components

  if (status === null) {
    return (
      <div className="mb-2 animate-pulse rounded-lg border border-border bg-surface px-2 py-3 text-sm text-muted">
        Checking download status…
      </div>
    );
  }

  return (
    <div className="relative mb-2 rounded-lg border border-border bg-surface py-3 pl-2 pr-10 shadow-sm transition-shadow hover:shadow-md">
      <div className="absolute right-2 top-2">
        <InvenioRDMFileActions
          download={download}
          editable={editable}
          fileId={fileId}
          status={status}
        />
      </div>

      <div className="min-w-0">
        <div
          className="truncate text-xs font-medium text-foreground"
          title={file.key}
        >
          {file.key}
        </div>
        {file.size ? (
          <div className="mt-0.5 text-xs text-muted">
            {(file.size / 1024 / 1024).toFixed(2)} MB
          </div>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium ${
            status.downloaded
              ? 'bg-success-subtle text-success'
              : 'bg-surface-subtle text-muted-strong'
          }`}
        >
          <span
            aria-hidden="true"
            className={`size-1.5 rounded-full ${
              status.downloaded ? 'bg-success-indicator' : 'bg-border-hover'
            }`}
          />
          {status.downloaded ? 'Downloaded' : 'Not downloaded'}
        </span>
        {!status.downloaded && (
          <button
            aria-label={`Download ${file.key} in JupyterServer`}
            className="inline-flex items-center gap-1.5 rounded-md border border-primary bg-primary px-2.5 py-1 text-xs font-medium text-on-primary transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            onClick={download}
            title="Download in JupyterServer"
            type="button"
          >
            <Download aria-hidden="true" size={14} />
            Download
          </button>
        )}
      </div>
      {downloadId ? (
        <div className="mt-3">
          <JobProgress jobId={downloadId} />
        </div>
      ) : null}
    </div>
  );
};
