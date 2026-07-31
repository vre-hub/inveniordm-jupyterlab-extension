import React from 'react';

import { createZenodoRecordVersion, ZenodoRecordVersion } from '../api_calls';
import { useServerSettings } from '../store';

export function CreateNewVersionButton({
  id,
  onCreated,
  versions,
  allowedToCreateNewVersion
}: {
  id: string;
  onCreated?: () => void | Promise<void>;
  versions: ZenodoRecordVersion[];
  allowedToCreateNewVersion: boolean;
}): JSX.Element {
  // check if the latest version is a draft or not. If it is, disable button
  const noNewVersionDraftExists =
    [...versions].sort(
      (a, b) =>
        b.versions.index - a.versions.index ||
        Number(b.is_draft) - Number(a.is_draft)
    )?.[0]?.is_draft === false;

  const disable = !allowedToCreateNewVersion || !noNewVersionDraftExists;
  const hint = !allowedToCreateNewVersion
    ? 'You do not have permission to create a new version.'
    : !noNewVersionDraftExists
      ? 'A new version draft already exists.'
      : '';

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
        disabled={disable}
        onClick={() => void createVersion()}
        type="button"
        title={hint}
      >
        {isLoading ? 'Creating...' : 'Create New Version'}
      </button>
      {error ? <span>{error}</span> : null}
    </>
  );
}
