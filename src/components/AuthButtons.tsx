import React from 'react';

import { useOpenAuth } from '../core/useOpenAuth';

type AuthButtonProps = {
  sandbox: boolean;
};

export const LoginButton: React.FC<AuthButtonProps> = ({ sandbox }) => {
  const openAuth = useOpenAuth(sandbox);

  return (
    <button onClick={() => openAuth('login')} type="button">
      Log in {sandbox ? '(sandbox)' : ''}
    </button>
  );
};

export const LogoutButton: React.FC<AuthButtonProps> = ({ sandbox }) => {
  const openAuth = useOpenAuth(sandbox);

  return (
    <button onClick={() => openAuth('logout')} type="button">
      Log out {sandbox ? '(sandbox)' : ''}
    </button>
  );
};

export const AuthButtons: React.FC<AuthButtonProps> = ({ sandbox }) => {
  return (
    <div>
      <LoginButton sandbox={sandbox} />
      <LogoutButton sandbox={sandbox} />
    </div>
  );
};
