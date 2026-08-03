import React from 'react';

import { ZenodoFileIdentifier } from '../api_calls';
import { ZenodoFileImportCellButton } from './ZenodoFileImportCell';
import { useDeleteDownload, useDownloadStatus } from '../core';

export const ZenodoFileDownloadStatus: React.FC<{
  fileId: ZenodoFileIdentifier;
}> = ({ fileId }) => {
  const { status } = useDownloadStatus(fileId);
  const { deleteDownload } = useDeleteDownload(fileId);

  if (status === null) {
    return <div>Checking download status...</div>;
  }

  return (
    <div>
      {status.downloaded ? 'Downloaded' : 'Not downloaded'}
      {status.path ? `: ${status.path}` : null}
      {status.downloaded ? (
        <button onClick={deleteDownload} type="button">
          Delete download
        </button>
      ) : null}
      {status.downloaded && <ZenodoFileImportCellButton fileId={fileId} />}
    </div>
  );
};
