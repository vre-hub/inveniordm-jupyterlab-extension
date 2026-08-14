import React from 'react';
import {
  InvenioRDMRecordVersion,
  createInvenioRDMRecordVersion
} from '../api_calls';
import { useServerSettings } from '../store';

/**
 * Custom hook to create a new version of a InvenioRDM record.
 *
 * @param versions - The list of versions of the record.
 * @param allowedToCreateNewVersion - Whether the user is allowed to create a new version.
 * @returns An object containing the createVersion function, loading state, error state, disable state, and hint message.
 */
export function useCreateNewVersion(
  versions: InvenioRDMRecordVersion[],
  allowedToCreateNewVersion: boolean
) {
  // check if the latest version is a draft or not. If it is, disable button
  const latestVersion =
    versions.length > 0
      ? [...versions].sort(
          (a, b) =>
            b.versions.index - a.versions.index ||
            Number(b.is_draft) - Number(a.is_draft)
        )[0]
      : null;

  const noNewVersionDraftExists = latestVersion?.is_draft === false;

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
      if (!latestVersion) {
        throw new Error(
          'No record versions available to create a new version from.'
        );
      }
      // we pass the latest version id here because passing any other ID can lead to a wrong version index in some deployments
      await createInvenioRDMRecordVersion(serverSettings, latestVersion.id);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  return {
    createVersion,
    isLoading,
    error,
    disable,
    hint
  };
}
