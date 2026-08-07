import { useServerSettings } from '../store';
import { getRemoteServersDefault } from '../api_calls';
import React from 'react';

type RemoteServerOption = {
  id: string;
  label: string;
};

export function useGetRemoteServersDefault(): RemoteServerOption | undefined {
  const serverSettings = useServerSettings();
  const [defaultRemoteServer, setDefaultRemoteServer] = React.useState<
    RemoteServerOption | undefined
  >(undefined);

  React.useEffect(() => {
    getRemoteServersDefault(serverSettings).then(def =>
      setDefaultRemoteServer(def)
    );
  }, [serverSettings]);

  return defaultRemoteServer;
}
