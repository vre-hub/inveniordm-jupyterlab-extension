import React from 'react';
import { useServerSettings } from '../store';
import { unsetInvenioRDMDownloadDirectory } from '../api_calls';

/** Provides an action for restoring the default download directory. */
export function useUnsetInvenioRDMDownloadDirectory() {
  const serverSettings = useServerSettings();
  const unsetDownloadDirectory = React.useCallback(() => {
    unsetInvenioRDMDownloadDirectory(serverSettings);
  }, [serverSettings]);
  return { unsetDownloadDirectory };
}
