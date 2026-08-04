import React from 'react';
import { PickDirectoryButton } from './DirectoryPicker';
import {
  useSetZenodoDownloadDirectory,
  useUnsetZenodoDownloadDirectory,
  useZenodoDownloadDirectory
} from '../core';

/**
 * Allows the user to select a download directory for Zenodo downloads.
 */
export function SelectDownloadDirectory() {
  const { setDownloadDirectory } = useSetZenodoDownloadDirectory();
  const { unsetDownloadDirectory } = useUnsetZenodoDownloadDirectory();
  const { downloadDirectory, reload } = useZenodoDownloadDirectory();

  return (
    <>
      <div>Current download directory: {downloadDirectory}</div>
      <PickDirectoryButton
        buttonText="Select download directory"
        onDirectorySelected={async dir => {
          await setDownloadDirectory(dir);
          await reload();
        }}
      />
      <button
        onClick={async () => {
          await unsetDownloadDirectory();
          await reload();
        }}
        type="button"
      >
        Reset to default download directory
      </button>
    </>
  );
}
