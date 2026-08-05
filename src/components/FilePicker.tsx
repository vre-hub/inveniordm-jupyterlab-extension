import React from 'react';
import { Upload } from 'lucide-react';

import { usePickUploadFiles } from '../store';

type PickFilesButtonProps = {
  buttonText: string;
  disabled?: boolean;
  onFilesSelected: (files: string[]) => void;
};

export function PickFilesButton({
  buttonText,
  disabled = false,
  onFilesSelected
}: PickFilesButtonProps): JSX.Element {
  const pickUploadFiles = usePickUploadFiles();

  const selectFiles = async (): Promise<void> => {
    const files = await pickUploadFiles();

    if (!files) {
      return;
    }

    onFilesSelected(files);
  };

  return (
    <div className="box-border w-full rounded-lg border border-dashed border-border-strong bg-surface-muted p-2">
      <button
        className="group flex w-full cursor-pointer items-center justify-center gap-3 rounded-md border-0 bg-surface px-4 py-2 text-left text-foreground-secondary shadow-sm transition-colors hover:bg-primary-subtle hover:text-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled}
        onClick={selectFiles}
        type="button"
      >
        <Upload className="size-4 shrink-0" aria-hidden="true" />
        <span className="flex flex-col gap-0.5">
          <span className="text-sm font-medium">{buttonText}</span>
          <span className="text-xs font-normal text-muted group-hover:text-primary">
            Choose files from JupyterLab
          </span>
        </span>
      </button>
    </div>
  );
}
