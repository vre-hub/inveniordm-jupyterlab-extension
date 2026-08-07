import React from 'react';
import { KeyRound, ShieldCheck } from 'lucide-react';

import { LoginButton, LogoutButton } from './AuthButtons';
import { ZenodoSandboxOverrideSetting } from './ZenodoSandboxOverrideSetting';
import { ZenodoUserProfile } from './ZenodoUserProfile';
import { useAccessTokenStatus } from '../api_calls';
import { LoadingPanel } from './LoadingPanel';

export const ZenodoLoginForm: React.FC = () => {
  const accessStatus = useAccessTokenStatus();

  if (!accessStatus) {
    return <LoadingPanel text="Checking Zenodo login status…" />;
  }

  const loggedIn =
    accessStatus &&
    accessStatus.access_token_present &&
    accessStatus.access_token_valid;

  return (
    <div>
      {!loggedIn && (
        <div className="px-3 py-5">
          <div className="mb-4 flex size-11 items-center justify-center rounded-full bg-primary-subtle text-primary">
            <KeyRound aria-hidden="true" className="size-5" />
          </div>
          <h2 className="m-0 text-sm font-semibold text-foreground">
            Connect your Zenodo account
          </h2>
          <p className="mb-5 mt-1.5 text-sm leading-5 text-muted-strong">
            Log in to access your account, manage records, and upload files.
          </p>
          <div className="mb-4">
            <ZenodoSandboxOverrideSetting />
          </div>
          <LoginButton />
        </div>
      )}
      {loggedIn && (
        <div className="px-3 py-4">
          <ZenodoUserProfile />
          {accessStatus.remote_server_id === 'zenodo_sandbox' && (
            <div className="mb-4 mt-3 flex items-center gap-2 rounded-md bg-warning-subtle px-3 py-2 text-xs font-medium text-warning-strong">
              <ShieldCheck aria-hidden="true" className="size-4 shrink-0" />
              Connected to the Zenodo sandbox environment
            </div>
          )}
          <div className="mb-4 mt-3">
            <ZenodoSandboxOverrideSetting />
          </div>
          <LogoutButton />
        </div>
      )}
    </div>
  );
};
