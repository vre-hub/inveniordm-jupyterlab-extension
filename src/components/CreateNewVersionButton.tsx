import React from 'react';

import { ZenodoRecordVersion } from '../api_calls';
import { useCreateNewVersion } from '../core/useCreateNewVersion';

export function CreateNewVersionButton({
  versions,
  allowedToCreateNewVersion
}: {
  versions: ZenodoRecordVersion[];
  allowedToCreateNewVersion: boolean;
}): JSX.Element {
  const { createVersion, isLoading, error, disable, hint } =
    useCreateNewVersion(versions, allowedToCreateNewVersion);

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
