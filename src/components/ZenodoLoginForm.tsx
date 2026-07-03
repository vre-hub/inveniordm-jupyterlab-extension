import React from 'react';

import { AuthButtons } from './AuthButtons';
import { LoginStatusPill } from './LoginStatusPill';
import { ZenodoUserProfile } from './ZenodoUserProfile';

export const ZenodoLoginForm: React.FC = () => {
  return (
    <>
      <LoginStatusPill />
      <AuthButtons sandbox={false} />
      <hr />
      <ZenodoUserProfile />
    </>
  );
};
