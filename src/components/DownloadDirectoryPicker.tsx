import React from 'react';
import {
  setZenodoDownloadDirectory,
  unsetZenodoDownloadDirectory
} from '../api_calls';
import { useServerSettings } from '../store';
import { PickDirectoryButton } from './DirectoryPicker';

/**
 * Allows the user to select a download directory for Zenodo downloads.
 */
export function SelectDownloadDirectory() {
  const serverSettings = useServerSettings();
  return (
    <>
      <PickDirectoryButton
        buttonText="Select download directory"
        onDirectorySelected={dir =>
          setZenodoDownloadDirectory(serverSettings, dir)
        }
      />
      <button
        onClick={() => unsetZenodoDownloadDirectory(serverSettings)}
        type="button"
      >
        Reset to default download directory
      </button>
    </>
  );
}
