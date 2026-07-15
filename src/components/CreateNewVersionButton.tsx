import React from 'react';

import { createZenodoRecordVersion } from '../api_calls';
import { useServerSettings } from '../store';

export function CreateNewVersionButton({
  id,
  onCreated
}: {
  id: string;
  onCreated?: () => void | Promise<void>;
}): JSX.Element {
  const serverSettings = useServerSettings();
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const createVersion = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await createZenodoRecordVersion(serverSettings, id);
      await onCreated?.();
    } catch (reason) {
      setError(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <button
        disabled={isLoading}
        onClick={() => void createVersion()}
        type="button"
      >
        {isLoading ? 'Creating...' : 'Create New Version'}
      </button>
      {error ? <span>{error}</span> : null}
    </>
  );
}
