import React from 'react';

import {
  getZenodoFileDownloadStatus,
  ZenodoFileDownloadStatusResponse
} from '../api_calls';
import { useServerSettings } from '../store';

export const ZenodoFileDownloadStatus: React.FC<{
  depositionId: number;
  fileId: string;
}> = ({ depositionId, fileId }) => {
  const serverSettings = useServerSettings();
  const [status, setStatus] =
    React.useState<ZenodoFileDownloadStatusResponse | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const poll = async (): Promise<void> => {
      const nextStatus = await getZenodoFileDownloadStatus(
        serverSettings,
        depositionId,
        fileId
      );
      if (isMounted) {
        setStatus(nextStatus);
      }
    };

    setStatus(null);
    const interval = window.setInterval(poll, 2000);
    poll();

    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, [depositionId, fileId, serverSettings]);

  if (status === null) {
    return <div>Checking download status...</div>;
  }

  return (
    <div>
      {status.downloaded ? 'Downloaded' : 'Not downloaded'}
      {status.path ? `: ${status.path}` : null}
    </div>
  );
};
