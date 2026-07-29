import React from 'react';

import {
  deleteZenodoFileDownload,
  getZenodoFileDownloadStatus,
  ZenodoFileDownloadStatusResponse,
  ZenodoFileIdentifier
} from '../api_calls';
import { useEventListener } from '../sse';
import { useServerSettings } from '../store';

function encodeTopicPart(value: string): string {
  return encodeURIComponent(value).replace(
    /[!'()*]/g,
    character => `%${character.charCodeAt(0).toString(16).toUpperCase()}`
  );
}

function downloadStatusChangedTopic(fileId: ZenodoFileIdentifier): string {
  return [
    'file.download-status.changed',
    encodeTopicPart(fileId.record_id),
    encodeTopicPart(fileId.record_status),
    encodeTopicPart(fileId.file_key)
  ].join('.');
}

export const ZenodoFileDownloadStatus: React.FC<{
  fileId: ZenodoFileIdentifier;
}> = ({ fileId }) => {
  const serverSettings = useServerSettings();
  const [status, setStatus] =
    React.useState<ZenodoFileDownloadStatusResponse | null>(null);

  const reloadStatus = React.useCallback(async (): Promise<void> => {
    setStatus(await getZenodoFileDownloadStatus(serverSettings, fileId));
  }, [fileId, serverSettings]);

  React.useEffect(() => {
    void reloadStatus();
  }, [reloadStatus]);

  useEventListener(downloadStatusChangedTopic(fileId), () => {
    void reloadStatus();
  });

  const deleteDownload = async (): Promise<void> => {
    await deleteZenodoFileDownload(serverSettings, fileId);
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
