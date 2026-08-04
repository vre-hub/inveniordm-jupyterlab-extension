import React from 'react';

import { LoginButton, LogoutButton } from './AuthButtons';
import { ZenodoUserProfile } from './ZenodoUserProfile';
import { useAccessTokenStatus } from '../api_calls';

export const ZenodoLoginForm: React.FC = () => {
  const accessStatus = useAccessTokenStatus();

  if (!accessStatus) {
    return <span>Loading...</span>;
  }

  const loggedIn =
    accessStatus &&
    accessStatus.access_token_present &&
    accessStatus.access_token_valid;

  return (
    <>
      {!loggedIn && (
        <div>
          <p>Log in to Zenodo to access your account and upload records.</p>
          <LoginButton sandbox={false} />
        </div>
      )}
      {loggedIn && (
        <div>
          <ZenodoUserProfile />
          {accessStatus.sandbox && (
            <p>You are logged in to the sandbox environment.</p>
          )}
          <LogoutButton sandbox={false} />
        </div>
      )}
    </>
  );
};
