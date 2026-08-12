import React from 'react';
import { KeyRound, ShieldCheck } from 'lucide-react';

import { LoginButton, LogoutButton } from './AuthButtons';
import { InvenioRDMRemoteServerDropdown } from './InvenioRDMRemoteServerDropdown';
import { InvenioRDMUserProfile } from './InvenioRDMUserProfile';
import { useAccessTokenStatus } from '../api_calls';
import { RemoteServerId } from '../remoteServers';
import { LoadingPanel } from './LoadingPanel';
import {
  useGetRemoteServersDefault,
  useRemoteServers,
  useShouldShowRemoteServerDropdownForLogin
} from '../core';
import { ErrorPanel } from './ErrorPanel';

export const InvenioRDMLoginForm: React.FC = () => {
  const accessStatus = useAccessTokenStatus();
  const [loginRemoteServer, setLoginRemoteServer] = React.useState<
    RemoteServerId | undefined
  >();
  const remoteServers = useRemoteServers();

  // Get the default remote server and set it as the initial value for loginRemoteServer
  const defaultOption = useGetRemoteServersDefault();
  React.useEffect(() => {
    if (defaultOption) {
      setLoginRemoteServer(defaultOption.id as RemoteServerId);
    }
  }, [defaultOption]);

  const showDropdown = useShouldShowRemoteServerDropdownForLogin();
  const selectedRemoteServer = remoteServers.find(
    server => server.id === loginRemoteServer
  );
  const loginAvailable =
    selectedRemoteServer?.login_available ?? defaultOption?.login_available;

  if (!accessStatus) {
    return <LoadingPanel text={`Checking login status…`} />;
  }

  if ('error' in accessStatus) {
    return <ErrorPanel error={accessStatus.error} />;
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
            Connect your Account
          </h2>
          <p className="mb-5 mt-1.5 text-sm leading-5 text-muted-strong">
            Log in to access your account, manage records, and upload files.
          </p>
          {showDropdown && (
            <div className="mb-4">
              <label className="block">
                <span className="block text-sm font-medium text-foreground-secondary">
                  Select environment
                </span>
                <span className="mt-1 block text-xs leading-5 text-muted">
                  Choose the environment to log into for this session.
                </span>
                <div className="mt-2">
                  <InvenioRDMRemoteServerDropdown
                    ariaLabel={`Login environment`}
                    onChange={setLoginRemoteServer}
                    value={loginRemoteServer}
                    useDefaultOption={false}
                  />
                </div>
              </label>
            </div>
          )}
          {loginAvailable === false && (
            <p className="mb-0 rounded-md bg-surface-muted px-3 py-2 text-sm text-muted-strong">
              Login for {selectedRemoteServer?.label} is not configured.
            </p>
          )}
          {loginAvailable !== false && (
            <LoginButton remoteServerId={loginRemoteServer} />
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
          <LogoutButton remoteServerId={loginRemoteServer} />
        </div>
      )}
    </div>
  );
};
