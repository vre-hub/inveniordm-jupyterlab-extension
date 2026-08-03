import React from 'react';
import {
  ZenodoFileIdentifier,
  getLatestActiveJobId,
  downloadZenodoFile
} from '../api_calls';
import { useServerSettings } from '../store';

export function useDownloadZenodoFile(fileId: ZenodoFileIdentifier) {
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

  return { download, downloadId };
}
