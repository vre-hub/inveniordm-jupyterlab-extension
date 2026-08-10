import React from 'react';

import { CurrentRemoteServer, getCurrentRemoteServer } from '../api_calls';
import { useEventListener } from '../sse';
import { useRemoteServerOverride, useServerSettings } from '../store';

/** Return the remote server used by extension API requests. */
export function useCurrentRemoteServer(): CurrentRemoteServer | undefined {
  const serverSettings = useServerSettings();
  const remoteServerOverride = useRemoteServerOverride();
  const [remoteServer, setRemoteServer] = React.useState<CurrentRemoteServer>();
  const requestId = React.useRef(0);

  const reload = React.useCallback(async (): Promise<void> => {
    const currentRequestId = ++requestId.current;
    try {
      const currentRemoteServer = await getCurrentRemoteServer(serverSettings);
      if (currentRequestId === requestId.current) {
        setRemoteServer(currentRemoteServer);
      }
    } catch {
      if (currentRequestId === requestId.current) {
        setRemoteServer(undefined);
      }
    }
  }, [serverSettings, remoteServerOverride]);

  React.useEffect(() => {
    void reload();
    return () => {
      requestId.current += 1;
    };
  }, [reload]);

  useEventListener('auth.status.changed', () => {
    void reload();
  });

  return remoteServer;
}
