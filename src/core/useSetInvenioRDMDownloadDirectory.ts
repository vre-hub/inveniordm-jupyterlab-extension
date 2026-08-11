import React from 'react';
import { setInvenioRDMDownloadDirectory } from '../api_calls';
import { useServerSettings } from '../store';

export function useSetInvenioRDMDownloadDirectory() {
  const serverSettings = useServerSettings();
  const setDownloadDirectory = React.useCallback(
    (dir: string) => {
      setInvenioRDMDownloadDirectory(serverSettings, dir);
    },
    [serverSettings]
  );
  return { setDownloadDirectory };
}
