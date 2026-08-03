import React from 'react';
import {
  ZenodoFileIdentifier,
  ZenodoFileDownloadStatusResponse,
  getZenodoFileDownloadStatus
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

export function useDownloadStatus(fileId: ZenodoFileIdentifier) {
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

  return { status };
}
