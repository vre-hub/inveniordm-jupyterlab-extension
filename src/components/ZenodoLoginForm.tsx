import React from 'react';
import { KeyRound, LoaderCircle, ShieldCheck } from 'lucide-react';

import { LoginButton, LogoutButton } from './AuthButtons';
import { ZenodoUserProfile } from './ZenodoUserProfile';
import { useAccessTokenStatus } from '../api_calls';

export const ZenodoLoginForm: React.FC = () => {
  const accessStatus = useAccessTokenStatus();

  if (!accessStatus) {
    return (
      <div
        aria-live="polite"
        className="flex items-center justify-center gap-2 rounded-lg border border-border bg-surface-muted px-4 py-8 text-sm font-medium text-muted shadow-sm"
      >
        <LoaderCircle
          aria-hidden="true"
          className="size-5 animate-spin text-primary"
        />
        Checking your login status…
      </div>
    );
  }

  const loggedIn =
    accessStatus &&
    accessStatus.access_token_present &&
    accessStatus.access_token_valid;

  return (
    <div>
      {!loggedIn && (
        <div className="p-5">
          <div className="mb-4 flex size-11 items-center justify-center rounded-full bg-primary-subtle text-primary">
            <KeyRound aria-hidden="true" className="size-5" />
          </div>
          <h2 className="m-0 text-base font-semibold text-foreground">
            Connect your Zenodo account
          </h2>
          <p className="mb-5 mt-1.5 text-sm leading-5 text-muted-strong">
            Log in to access your account, manage records, and upload files.
          </p>
          <LoginButton sandbox={false} />
        </div>
      )}
      {loggedIn && (
        <div className="p-4">
          <ZenodoUserProfile />
          {accessStatus.sandbox && (
            <div className="mb-4 mt-3 flex items-center gap-2 rounded-md bg-warning-subtle px-3 py-2 text-xs font-medium text-warning-strong">
              <ShieldCheck aria-hidden="true" className="size-4 shrink-0" />
              Connected to the Zenodo sandbox environment
            </div>
          )}
          <LogoutButton sandbox={false} />
        </div>
      )}
    </div>
  );
};
