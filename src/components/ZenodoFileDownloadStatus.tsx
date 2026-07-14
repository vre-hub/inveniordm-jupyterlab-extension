import React from 'react';

import {
  deleteZenodoFileDownload,
  getZenodoFileDownloadStatus,
  ZenodoFileDownloadStatusResponse
} from '../api_calls';
import { useEventListener } from '../sse';
import { useServerSettings } from '../store';

function encodeTopicPart(value: string): string {
  return encodeURIComponent(value).replace(
    /[!'()*]/g,
    character => `%${character.charCodeAt(0).toString(16).toUpperCase()}`
  );
}

function downloadStatusChangedTopic(recordId: string, fileKey: string): string {
  return [
    'file.download-status.changed',
    encodeTopicPart(String(recordId)),
    encodeTopicPart(fileKey)
  ].join('.');
}

export const ZenodoFileDownloadStatus: React.FC<{
  recordId: string;
  fileKey: string;
}> = ({ recordId, fileKey }) => {
  const serverSettings = useServerSettings();
  const [status, setStatus] =
    React.useState<ZenodoFileDownloadStatusResponse | null>(null);

  const reloadStatus = React.useCallback(async (): Promise<void> => {
    setStatus(
      await getZenodoFileDownloadStatus(serverSettings, recordId, fileKey)
    );
  }, [recordId, fileKey, serverSettings]);

  React.useEffect(() => {
    void reloadStatus();
  }, [reloadStatus]);

  useEventListener(downloadStatusChangedTopic(recordId, fileKey), () => {
    void reloadStatus();
  });

  const deleteDownload = async (): Promise<void> => {
    await deleteZenodoFileDownload(serverSettings, recordId, fileKey);
  };

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
    </div>
  );
};
