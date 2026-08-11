import { constructInvenioRDMAuthUrl } from '../api_calls';
import { RemoteServerId } from '../remoteServers';
import { useServerSettings, useRemoteServerOverride } from '../store';

export const useOpenAuth = (
  remoteServerId?: RemoteServerId
): ((action: 'login' | 'logout') => void) => {
  const serverSettings = useServerSettings();
  const remoteServerOverride = useRemoteServerOverride();

  return (action: 'login' | 'logout'): void => {
    window.location.href = constructInvenioRDMAuthUrl(
      serverSettings,
      action,
      window.location.href,
      remoteServerId ?? remoteServerOverride
    );
  };
};
