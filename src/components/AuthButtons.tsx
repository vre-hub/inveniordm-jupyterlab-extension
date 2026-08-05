import React from 'react';
import { LogIn, LogOut } from 'lucide-react';

import { useOpenAuth } from '../core';

type AuthButtonProps = {
  sandbox: boolean;
};

export const LoginButton: React.FC<AuthButtonProps> = ({ sandbox }) => {
  const openAuth = useOpenAuth(sandbox);

  return (
    <button
      className="box-border inline-flex w-full items-center justify-center gap-2 rounded-md border border-primary bg-primary px-2 py-2.5 text-sm font-semibold text-on-primary shadow-sm transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      onClick={() => openAuth('login')}
      type="button"
    >
      <LogIn aria-hidden="true" className="size-4 shrink-0" />
      Log in{sandbox ? ' to sandbox' : ''}
    </button>
  );
};

export const LogoutButton: React.FC<AuthButtonProps> = ({ sandbox }) => {
  const openAuth = useOpenAuth(sandbox);

  return (
    <button
      className="box-border inline-flex w-full items-center justify-center gap-2 rounded-md border border-border-strong bg-surface px-2 py-2.5 text-sm font-semibold text-foreground-secondary shadow-sm transition-colors hover:border-border-hover hover:bg-surface-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      onClick={() => openAuth('logout')}
      type="button"
    >
      <LogOut aria-hidden="true" className="size-4 shrink-0" />
      Log out{sandbox ? ' of sandbox' : ''}
    </button>
  );
};

export const AuthButtons: React.FC<AuthButtonProps> = ({ sandbox }) => {
  return (
    <div className="flex flex-col gap-2">
      <LoginButton sandbox={sandbox} />
      <LogoutButton sandbox={sandbox} />
    </div>
  );
};
