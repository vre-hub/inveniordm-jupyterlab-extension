import React from 'react';
import { LogIn, LogOut } from 'lucide-react';

import { useOpenAuth } from '../core';
import { RemoteServerId } from '../remoteServers';

type AuthButtonProps = {
  remoteServerId?: RemoteServerId;
};

/** Opens the login flow for an InvenioRDM server. */
export const LoginButton: React.FC<AuthButtonProps> = ({ remoteServerId }) => {
  const openAuth = useOpenAuth(remoteServerId);

  return (
    <button
      className="box-border inline-flex w-full items-center justify-center gap-2 rounded-md border border-primary bg-primary px-2 py-2.5 text-sm font-semibold text-on-primary shadow-sm transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      onClick={() => openAuth('login')}
      type="button"
    >
      <LogIn aria-hidden="true" className="size-4 shrink-0" />
      Log in
    </button>
  );
};

/** Opens the logout flow for an InvenioRDM server. */
export const LogoutButton: React.FC<AuthButtonProps> = ({ remoteServerId }) => {
  const openAuth = useOpenAuth(remoteServerId);

  return (
    <button
      className="box-border inline-flex w-full items-center justify-center gap-2 rounded-md border border-border-strong bg-surface px-2 py-2.5 text-sm font-semibold text-foreground-secondary shadow-sm transition-colors hover:border-border-hover hover:bg-surface-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      onClick={() => openAuth('logout')}
      type="button"
    >
      <LogOut aria-hidden="true" className="size-4 shrink-0" />
      Log out
    </button>
  );
};
