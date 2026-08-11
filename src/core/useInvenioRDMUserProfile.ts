import React from 'react';
import {
  InvenioRDMMeResponse,
  getInvenioRDMMe,
  useAccessTokenEventListener
} from '../api_calls';
import { useServerSettings } from '../store';

export function useInvenioRDMUserProfile() {
  const serverSettings = useServerSettings();
  const [profile, setProfile] = React.useState<InvenioRDMMeResponse | null>(null);
  const [error, setError] = React.useState('');

  async function loadProfile(): Promise<void> {
    try {
      setProfile(await getInvenioRDMMe(serverSettings));
    } catch (reason) {
      setProfile(null);
      setError(String(reason));
    } finally {
    }
  }

  // Load the profile initially.
  React.useEffect(() => {
    void loadProfile();
  }, [serverSettings]);

  // Update the profile when the access token changes, which may change the user.
  useAccessTokenEventListener(() => {
    loadProfile();
  });

  return { profile, error };
}
