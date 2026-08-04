import React from 'react';
import { Copy, Download, FileCode2, HardDrive, Trash2 } from 'lucide-react';

import { JobProgress } from './JobProgress';
import { OverflowMenu, OverflowMenuItem } from './OverflowMenu';
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

  const { download, downloadId } = useDownloadZenodoFile(fileId); // TODO both the download button and the status need this, fix if we want to split this into separate components

  const copyFilePath = React.useCallback(async (): Promise<void> => {
    if (status?.path) {
      await navigator.clipboard.writeText(status.path);
    }
  }, [status?.path]);

  if (status === null) {
    return (
      <div className="mb-2 animate-pulse rounded-lg border border-border bg-surface p-4 text-sm text-muted">
        Checking download status…
      </div>
    );
  }

  const actions: OverflowMenuItem[] = [
    {
      label: 'Download in JupyterServer',
      hint: status.downloaded
        ? 'File is already downloaded.'
        : 'Save this file to the Jupyter server.',
      icon: <Download size={16} />,
      onClick: download,
      disabled: status.downloaded !== false
    },
    ...(status.downloaded
      ? [
          {
            label: 'Delete download',
            hint: 'Remove the local copy from the Jupyter server.',
            icon: <HardDrive size={16} />,
            onClick: deleteDownload,
            destructive: true
          },
          {
            label: 'Copy File Path',
            hint: 'Copy the path to this file to the clipboard.',
            icon: <Copy size={16} />,
            onClick: copyFilePath,
            disabled: !status.path
          },
          {
            label: 'Insert Cell with File Path',
            hint: 'Add a notebook cell that hardcodes the path to this file.',
            icon: <FileCode2 size={16} />,
            onClick: insertImportCell
          }
        ]
      : []),
    ...(editable
      ? [
          {
            label: isDeleting ? 'Deleting…' : 'Delete from Zenodo',
            hint: 'Permanently remove this file from the Zenodo record.',
            icon: <Trash2 size={16} />,
            onClick: deleteFile,
            disabled: isDeleting,
            destructive: true
          }
        ]
      : [])
  ];

  return (
    <div className="relative mb-2 rounded-lg border border-border bg-surface p-4 pr-12 shadow-sm transition-shadow hover:shadow-md">
      <div className="absolute right-3 top-3">
        <OverflowMenu items={actions} label={`Actions for ${file.key}`} />
      </div>

      <div className="min-w-0">
        <div
          className="truncate text-sm font-semibold text-foreground"
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
