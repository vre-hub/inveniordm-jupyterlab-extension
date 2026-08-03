import { constructZenodoAuthUrl } from '../api_calls';
import { useServerSettings } from '../store';

export const useOpenAuth = (
  sandbox: boolean
): ((action: 'login' | 'logout') => void) => {
  const serverSettings = useServerSettings();

  return (action: 'login' | 'logout'): void => {
    window.location.href = constructZenodoAuthUrl(
      serverSettings,
      action,
      window.location.href,
      sandbox
    );
  };
};
