import React from 'react';
import { useServerSettings } from '../store';
import { unsetInvenioRDMDownloadDirectory } from '../api_calls';

export function useUnsetInvenioRDMDownloadDirectory() {
  const serverSettings = useServerSettings();
  const unsetDownloadDirectory = React.useCallback(() => {
    unsetInvenioRDMDownloadDirectory(serverSettings);
  }, [serverSettings]);
  return { unsetDownloadDirectory };
}
