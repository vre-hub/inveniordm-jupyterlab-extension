import React from 'react';

import { downloadZenodoFile, getLatestActiveJobId } from '../api_calls';
import { useServerSettings } from '../store';
import { JobProgress } from './JobProgress';
import { ZenodoFileDownloadStatus } from './ZenodoFileDownloadStatus';
import type { ZenodoFile, ZenodoFileIdentifier } from '../api_calls';
import { useZenodoFileIdentifierFromProps } from '../core/useZenodoFileIdentifierFromProps';
import { useDeleteZenodoFile } from '../core/useDeleteZenodoFile';

export const ZenodoFileInfo: React.FC<{
  file: ZenodoFile;
  recordId: string;
  isDraft: boolean;
  editable: boolean;
}> = ({ file, recordId, isDraft, editable }) => {
  const fileId = useZenodoFileIdentifierFromProps(file, recordId, isDraft);

  return (
    <div
      style={{
        border: '1px solid #000000',
        padding: '3px',
        marginBottom: '2px'
      }}
    >
      <ZenodoFileDetails file={file} />
      <ZenodoFileDownload fileId={fileId} />
      {editable && <ZenodoFileDeleteButton fileId={fileId} />}
    </div>
  );
};

const ZenodoFileDetails: React.FC<{
  file: ZenodoFile;
}> = ({ file }) => (
  <div>
    {file.key}
    {/* TODO display file size in a reasonable unit */}
    {file.size ? ` (${(file.size / 1024 / 1024).toFixed(2)} MB)` : null}
  </div>
);

// TODO refactor and extract
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
  const { deleteFile, isDeleting } = useDeleteZenodoFile(fileId);
  return (
    <>
      <button disabled={isDeleting} onClick={deleteFile} type="button">
        {isDeleting ? 'Deleting…' : 'Delete from Zenodo'}
      </button>
    </>
  );
};
