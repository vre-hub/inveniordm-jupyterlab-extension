import React from 'react';
import { PickDirectoryButton } from './DirectoryPicker';
import { useSetZenodoDownloadDirectory } from '../core/useSetZenodoDownloadDirectory';
import { useUnsetZenodoDownloadDirectory } from '../core/useUnsetZenodoDownloadDirectory';

/**
 * Allows the user to select a download directory for Zenodo downloads.
 */
export function SelectDownloadDirectory() {
  const { setDownloadDirectory } = useSetZenodoDownloadDirectory();
  const { unsetDownloadDirectory } = useUnsetZenodoDownloadDirectory();

  return (
    <>
      <PickDirectoryButton
        buttonText="Select download directory"
        onDirectorySelected={dir => setDownloadDirectory(dir)}
      />
      <button onClick={() => unsetDownloadDirectory()} type="button">
        Reset to default download directory
      </button>
    </>
  );
}
