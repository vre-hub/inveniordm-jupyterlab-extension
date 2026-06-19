import React from 'react';
import { ServerConnection } from '@jupyterlab/services';

import { getZenodoMe, ZenodoMeResponse } from '../api_calls';

interface IZenodoUserProfileProps {
  serverSettings: ServerConnection.ISettings;
}

export const ZenodoUserProfile: React.FC<IZenodoUserProfileProps> = ({
  serverSettings
}) => {
  const [profile, setProfile] = React.useState<ZenodoMeResponse | null>(null);
  const [message, setMessage] = React.useState('');

  async function loadProfile(): Promise<void> {
    try {
      setProfile(await getZenodoMe(serverSettings));
    } catch (reason) {
      setProfile(null);
      setMessage(String(reason));
    } finally {
    }
  }

  React.useEffect(() => {
    loadProfile();
    // TODO instead of polling log in status, use SSE
    setInterval(loadProfile, 1 * 1000);
  }, [serverSettings]);

  if (profile === null) {
    return (
      <div>
        {message ? <p>{message}</p> : null}
      </div>
    );
  }

  return (
    <div>
      <p>
        Zenodo user: <strong>{profile.email}</strong>
      </p>
    </div>
  );
};
