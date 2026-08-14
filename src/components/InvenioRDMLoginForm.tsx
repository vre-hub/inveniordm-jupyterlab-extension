import React from 'react';
import { KeyRound, ShieldCheck } from 'lucide-react';

import { LoginButton, LogoutButton } from './AuthButtons';
import { InvenioRDMUserProfile } from './InvenioRDMUserProfile';
import { useAccessTokenStatus } from '../api_calls';
import { LoadingPanel } from './LoadingPanel';
import {
  useGetRemoteServersDefault,
  useRemoteServers,
  useShouldShowRemoteServerDropdownForLogin
} from '../core';
import { useRemoteServerOverride } from '../store';
import { ErrorPanel } from './ErrorPanel';
import { InvenioRDMRemoteServerOverrideSetting } from './InvenioRDMRemoteServerOverrideSetting';

export const InvenioRDMLoginForm: React.FC = () => {
  const accessStatus = useAccessTokenStatus();
  const defaultOption = useGetRemoteServersDefault();
  const remoteServers = useRemoteServers();
  const remoteServerOverride = useRemoteServerOverride();
  const selectedRemoteServer = remoteServerOverride ?? defaultOption?.id;
  const selectedRemoteServerOption = remoteServers.find(
    server => server.id === selectedRemoteServer
  );
  const loginAvailable =
    selectedRemoteServerOption?.login_available ??
    defaultOption?.login_available;
  const shouldShowRemoteServerDropdown =
    useShouldShowRemoteServerDropdownForLogin();

  if (!accessStatus) {
    return (
      <div>
        <div className="border-b border-border px-3 pb-4">
          {shouldShowRemoteServerDropdown && (
            <InvenioRDMRemoteServerOverrideSetting />
          )}
        </div>
        <LoadingPanel text={`Checking login status…`} />
      </div>
    );
  }

  if ('error' in accessStatus) {
    return (
      <div>
        <div className="border-b border-border px-3 pb-4">
          {shouldShowRemoteServerDropdown && (
            <InvenioRDMRemoteServerOverrideSetting />
          )}
        </div>
        <ErrorPanel error={accessStatus.error} />
      </div>
    );
  }

  const loggedIn =
    accessStatus &&
    accessStatus.access_token_present &&
    accessStatus.access_token_valid;

  return (
    <div>
      <div className="px-3 pb-4">
        {shouldShowRemoteServerDropdown && (
          <InvenioRDMRemoteServerOverrideSetting />
        )}
      </div>
      {!loggedIn && (
        <div className="px-3 py-5">
          <div className="mb-4 flex size-11 items-center justify-center rounded-full bg-primary-subtle text-primary">
            <KeyRound aria-hidden="true" className="size-5" />
          </div>
          <h2 className="m-0 text-sm font-semibold text-foreground">
            Connect your Account
          </h2>
          <p className="mb-5 mt-1.5 text-sm leading-5 text-muted-strong">
            Log in to access your account, manage records, and upload files.
          </p>
          {loginAvailable === false && (
            <p className="mb-0 rounded-md bg-surface-muted px-3 py-2 text-sm text-muted-strong">
              Login for {selectedRemoteServerOption?.label} is not configured.
            </p>
          )}
          {loginAvailable !== false && (
            <LoginButton remoteServerId={selectedRemoteServer} />
          )}
        </div>
      )}
      {loggedIn && (
        <div className="px-3 py-4">
          <InvenioRDMUserProfile />
          <div className="mb-4 mt-3 flex items-center gap-2 rounded-md bg-warning-subtle px-3 py-2 text-xs font-medium text-warning-strong">
            <ShieldCheck aria-hidden="true" className="size-4 shrink-0" />

            <span>
              Connected to{' '}
              <a
                href={accessStatus.remote_server_base_url}
                className="font-semibold text-warning-strong underline underline-offset-2 transition-colors hover:text-warning"
                target="_blank"
              >
                {accessStatus.remote_server_label}
              </a>
            </span>
          </div>
          <LogoutButton remoteServerId={selectedRemoteServer} />
        </div>
      )}
    </div>
  );
};
