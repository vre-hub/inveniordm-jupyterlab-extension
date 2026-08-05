import { constructZenodoAuthUrl } from '../api_calls';
import { useServerSettings } from '../store';
import { RemoteServerId } from '../remoteServers';

export const useOpenAuth = (
  remoteServerId: RemoteServerId
): ((action: 'login' | 'logout') => void) => {
  const serverSettings = useServerSettings();

  return (action: 'login' | 'logout'): void => {
    window.location.href = constructZenodoAuthUrl(
      serverSettings,
      action,
      window.location.href,
      remoteServerId
    );
  };
};
