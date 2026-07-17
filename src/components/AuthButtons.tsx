import React from 'react';

import { constructZenodoAuthUrl } from '../api_calls';
import { useServerSettings } from '../store';

type AuthButtonsProps = {
  sandbox: boolean;
};

type AuthButtonProps = {
  sandbox: boolean;
};

const useOpenAuth = (
  sandbox: boolean
): ((action: 'login' | 'logout') => void) => {
  const serverSettings = useServerSettings();

  return (action: 'login' | 'logout'): void => {
    window.location.href = constructZenodoAuthUrl(
      serverSettings,
      action,
      window.location.href,
      sandbox
    );
  };
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

export const AuthButtons: React.FC<AuthButtonsProps> = ({ sandbox }) => {
  return (
    <div>
      <LoginButton sandbox={sandbox} />
      <LogoutButton sandbox={sandbox} />
    </div>
  );
};
