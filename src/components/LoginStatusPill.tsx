import React from 'react';
import { ServerConnection } from '@jupyterlab/services';

import { checkAccessStatus, AccessTokenResponse } from '../api_calls';


export type LoginStatus = 'Logged In' | 'Invalid Login' | 'Not Logged In';

function formatAccessStatus(status: AccessTokenResponse): LoginStatus {
  if (!status.access_token_present) {
    return 'Not Logged In';
  }

  return status.access_token_valid ? 'Logged In' : 'Invalid Login';
}

interface ILoginStatusPillProps {
  serverSettings: ServerConnection.ISettings;
}

export const LoginStatusPill: React.FC<ILoginStatusPillProps> = ({
  serverSettings
}) => {
  const [status, setStatus] = React.useState<LoginStatus>('Not Logged In');

  React.useEffect(() => {
    //TODO this is only called once, find a way to update the status without polling
    checkAccessStatus(serverSettings)
      .then(formatAccessStatus)
      .then(setStatus)
      .catch(() => setStatus('Invalid Login'));
  }, [serverSettings]);

  return (
    <span
      style={{ border: '1px solid #aaa', borderRadius: 12, padding: '2px 8px' }}
    >
      {status}
    </span>
  );
};
