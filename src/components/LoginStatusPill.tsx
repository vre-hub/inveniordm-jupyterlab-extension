import React from 'react';

import { AccessTokenResponse, useAccessTokenStatus } from '../api_calls';

export type LoginStatus = 'Logged In' | 'Invalid Login' | 'Not Logged In';

function formatAccessStatus(status: AccessTokenResponse): LoginStatus {
  if (!status.access_token_present) {
    return 'Not Logged In';
  }

  return status.access_token_valid ? 'Logged In' : 'Invalid Login';
}

export const LoginStatusPill: React.FC = () => {
  const accessStatus = useAccessTokenStatus()

  if (!accessStatus) {
    return <span>Loading...</span>;
  }

  const status = formatAccessStatus(accessStatus);
  const isSandbox = accessStatus.sandbox;

  return (
    <span
      style={{ border: '1px solid #aaa', borderRadius: 12, padding: '2px 8px' }}
    >

      {status} {isSandbox && '(Sandbox)'}
    </span>
  );
};
