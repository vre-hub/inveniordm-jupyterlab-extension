import React from 'react';
import { useServerSettings } from '../store';
import { unsetZenodoDownloadDirectory } from '../api_calls';

export function useUnsetZenodoDownloadDirectory() {
  const serverSettings = useServerSettings();
  const unsetDownloadDirectory = React.useCallback(() => {
    unsetZenodoDownloadDirectory(serverSettings);
  }, [serverSettings]);
  return { unsetDownloadDirectory };
}
