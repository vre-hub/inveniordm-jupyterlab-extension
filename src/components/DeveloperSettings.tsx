import React from 'react';

import { usePickDownloadDirectory } from '../store';
import { AuthButtons } from './AuthButtons';
import { ZenodoSandboxOverrideSetting } from './ZenodoSandboxOverrideSetting';

export function DeveloperSettings(): JSX.Element {
  const pickDownloadDirectory = usePickDownloadDirectory();
  const [error, setError] = React.useState<string | null>(null);

  const selectDownloadDirectory = async (): Promise<void> => {
    setError(null);
    const directory = await pickDownloadDirectory();

    if (!directory) {
      return;
    }

    console.log(`Selected download directory: ${directory}`);
  };

  return (
    <>
      <ZenodoSandboxOverrideSetting />
      <button onClick={selectDownloadDirectory} type="button">
        Select download directory
      </button>
      {error ? <p>Error: {error}</p> : null}
      <AuthButtons sandbox={true} />
    </>
  );
}
