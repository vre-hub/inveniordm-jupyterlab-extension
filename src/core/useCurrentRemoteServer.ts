import React from 'react';

import { CurrentRemoteServer, getCurrentRemoteServer } from '../api_calls';
import { useEventListener } from '../sse';
import { useRemoteServerOverride, useServerSettings } from '../store';

/** Return the remote server used by extension API requests. */
export function useCurrentRemoteServer(): {
  remoteServer: CurrentRemoteServer | undefined;
  isLoading: boolean;
  error: string | undefined;
} {
  const serverSettings = useServerSettings();
  const remoteServerOverride = useRemoteServerOverride();
  const [remoteServer, setRemoteServer] = React.useState<CurrentRemoteServer>();
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string>();
  const requestId = React.useRef(0);

  const reload = React.useCallback(async (): Promise<void> => {
    const currentRequestId = ++requestId.current;
    setIsLoading(true);
    setError(undefined);
    try {
      const currentRemoteServer = await getCurrentRemoteServer(serverSettings);
      if (currentRequestId === requestId.current) {
        setRemoteServer(currentRemoteServer);
        setIsLoading(false);
      }
    } catch (reason) {
      if (currentRequestId === requestId.current) {
        setRemoteServer(undefined);
        setError(String(reason));
        setIsLoading(false);
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

  return { remoteServer, isLoading, error };
}
