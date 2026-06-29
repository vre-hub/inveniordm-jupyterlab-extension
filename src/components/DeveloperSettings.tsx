import React from 'react';

import { AuthButtons } from './AuthButtons';
import { ZenodoSandboxOverrideSetting } from './ZenodoSandboxOverrideSetting';

export function DeveloperSettings(): JSX.Element {
  return (
    <>
      <ZenodoSandboxOverrideSetting />
      <AuthButtons sandbox={true} />
    </>
  );
}
