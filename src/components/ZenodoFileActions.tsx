import React from 'react';
import { Copy, Download, FileCode2, HardDrive, Trash2 } from 'lucide-react';

import type {
  ZenodoFileDownloadStatusResponse,
  ZenodoFileIdentifier
} from '../api_calls';
import {
  useDeleteDownload,
  useDeleteZenodoFile,
  useInsertImportCell
} from '../core';
import { OverflowMenu, OverflowMenuItem } from './OverflowMenu';

export const ZenodoFileActions: React.FC<{
  fileId: ZenodoFileIdentifier;
  status: ZenodoFileDownloadStatusResponse;
  editable: boolean;
  download: () => Promise<void>;
}> = ({ fileId, status, editable, download }) => {
  const { deleteDownload } = useDeleteDownload(fileId);
  const { insertImportCell } = useInsertImportCell(fileId);
  const { deleteFile, isDeleting } = useDeleteZenodoFile(fileId);

  const copyFilePath = React.useCallback(async (): Promise<void> => {
    if (status.path) {
      await navigator.clipboard.writeText(status.path);
    }
  }, [status.path]);

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
    <OverflowMenu items={actions} label={`Actions for ${fileId.file_key}`} />
  );
};
