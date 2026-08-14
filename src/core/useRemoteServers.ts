import React from 'react';

import { getRemoteServers, RemoteServerOption } from '../api_calls';
import { useServerSettings } from '../store';

/** Returns the InvenioRDM servers available to the extension. */
export function useRemoteServers(): RemoteServerOption[] {
  const serverSettings = useServerSettings();
  const [remoteServers, setRemoteServers] = React.useState<
    RemoteServerOption[]
  >([]);

  React.useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const servers = await getRemoteServers(serverSettings);
        if (!cancelled) {
          setRemoteServers(servers);
        }
      } catch {
        if (!cancelled) {
          setRemoteServers([]);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [serverSettings]);

  return remoteServers;
}
