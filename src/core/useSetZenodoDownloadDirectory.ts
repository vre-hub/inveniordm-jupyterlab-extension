import React from 'react';
import { setZenodoDownloadDirectory } from '../api_calls';
import { useServerSettings } from '../store';

export function useSetZenodoDownloadDirectory() {
  const serverSettings = useServerSettings();
  const setDownloadDirectory = React.useCallback(
    (dir: string) => {
      setZenodoDownloadDirectory(serverSettings, dir);
    },
    [serverSettings]
  );
  return { setDownloadDirectory };
}
