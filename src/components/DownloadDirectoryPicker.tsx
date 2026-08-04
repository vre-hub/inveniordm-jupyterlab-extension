import React, { useLayoutEffect, useRef } from 'react';
import { FolderOpen, RotateCcw } from 'lucide-react';
import {
  useSetZenodoDownloadDirectory,
  useUnsetZenodoDownloadDirectory,
  useZenodoDownloadDirectory
} from '../core';
import { usePickDownloadDirectory } from '../store';

const CURRENT_DIRECTORY_LABEL = 'Current download directory';
const SELECT_DIRECTORY_LABEL = 'Select download directory';
const RESET_DIRECTORY_LABEL = 'Reset to default download directory';

/**
 * Allows the user to select a download directory for Zenodo downloads.
 */
export function SelectDownloadDirectory() {
  const { setDownloadDirectory } = useSetZenodoDownloadDirectory();
  const { unsetDownloadDirectory } = useUnsetZenodoDownloadDirectory();
  const { downloadDirectory, reload } = useZenodoDownloadDirectory();
  const pickDownloadDirectory = usePickDownloadDirectory();
  const pathInputRef = useRef<HTMLInputElement>(null);

  const selectDownloadDirectory = async (): Promise<void> => {
    const directory = await pickDownloadDirectory();

    if (!directory) {
      return;
    }

    await setDownloadDirectory(directory);
    await reload();
  };

  useLayoutEffect(() => {
    const pathInput = pathInputRef.current;

    if (pathInput) {
      pathInput.scrollLeft = pathInput.scrollWidth;
    }
  }, [downloadDirectory]);

  return (
    <div className="mt-2 flex w-full min-w-0 items-center gap-2">
      <input
        aria-label={CURRENT_DIRECTORY_LABEL}
        className="box-border min-w-0 flex-1 rounded-md border border-border-strong bg-surface px-3 py-2 text-sm text-foreground-secondary shadow-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        readOnly
        ref={pathInputRef}
        title={downloadDirectory}
        type="text"
        value={downloadDirectory}
      />
      <button
        aria-label={SELECT_DIRECTORY_LABEL}
        className="box-border inline-flex size-8 shrink-0 items-center justify-center rounded-md border border-primary bg-primary text-on-primary shadow-sm transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        onClick={selectDownloadDirectory}
        title={SELECT_DIRECTORY_LABEL}
        type="button"
      >
        <FolderOpen aria-hidden="true" className="size-4" />
      </button>
      <button
        aria-label={RESET_DIRECTORY_LABEL}
        className="box-border inline-flex size-8 shrink-0 items-center justify-center rounded-md border border-border-strong bg-surface text-foreground-secondary shadow-sm transition-colors hover:border-border-hover hover:bg-surface-muted hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        onClick={async () => {
          await unsetDownloadDirectory();
          await reload();
        }}
        title={RESET_DIRECTORY_LABEL}
        type="button"
      >
        <RotateCcw aria-hidden="true" className="size-4" />
      </button>
    </div>
  );
}
