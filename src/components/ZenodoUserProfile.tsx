import React from 'react';

import {
  getZenodoMe,
  ZenodoMeResponse,
  useAccessTokenEventListener
} from '../api_calls';
import { useServerSettings } from '../store';

function useZenodoUserProfile() {
  const serverSettings = useServerSettings();
  const [profile, setProfile] = React.useState<ZenodoMeResponse | null>(null);
  const [error, setError] = React.useState('');

  async function loadProfile(): Promise<void> {
    try {
      setProfile(await getZenodoMe(serverSettings));
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

export const ZenodoUserProfile: React.FC = () => {
  const { profile, error } = useZenodoUserProfile();

  if (profile === null) {
    return <div>{error ? <p>{error}</p> : null}</div>;
  }

  return (
    <div>
      <p>
        Zenodo user: <strong>{profile.email}</strong>
      </p>
    </div>
  );
};
