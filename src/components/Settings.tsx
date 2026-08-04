import React from 'react';

import { AuthButtons } from './AuthButtons';
import { ZenodoSandboxOverrideSetting } from './ZenodoSandboxOverrideSetting';
import { SelectDownloadDirectory } from './DownloadDirectoryPicker';

export function Settings(): JSX.Element {
  return (
    <>
      <b>Download Directory: </b>
      <SelectDownloadDirectory />
      <hr />
      <b>Developer Settings</b>
      <br />
      <ZenodoSandboxOverrideSetting />
      <AuthButtons sandbox={true} />
    </>
  );
}
