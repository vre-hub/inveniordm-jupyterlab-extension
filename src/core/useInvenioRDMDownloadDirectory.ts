import React from 'react';
import { getInvenioRDMDownloadDirectory } from '../api_calls';
import { useServerSettings } from '../store';

export function useInvenioRDMDownloadDirectory() {
  const serverSettings = useServerSettings();
  const [downloadDirectory, setDownloadDirectory] = React.useState('');

  const reload = React.useCallback(async (): Promise<void> => {
    const response = await getInvenioRDMDownloadDirectory(serverSettings);
    setDownloadDirectory(response.downloads_dir);
  }, [serverSettings]);

  React.useEffect(() => {
    void reload();
  }, [reload]);

  return { downloadDirectory, reload };
}
