import { constructZenodoAuthUrl } from '../api_calls';
import { useServerSettings, useRemoteServerOverride } from '../store';

export const useOpenAuth = (): ((action: 'login' | 'logout') => void) => {
  const serverSettings = useServerSettings();
  const remoteServerOverride = useRemoteServerOverride();

  return (action: 'login' | 'logout'): void => {
    window.location.href = constructZenodoAuthUrl(
      serverSettings,
      action,
      window.location.href,
      remoteServerOverride ?? 'zenodo_production'
    );
  };
};
