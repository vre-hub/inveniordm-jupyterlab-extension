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
    <div className="box-border w-full rounded-lg border border-dashed border-slate-300 bg-slate-50 p-2">
      <button
        className="group flex w-full cursor-pointer items-center justify-center gap-3 rounded-md border-0 bg-white px-4 py-2 text-left text-slate-700 shadow-sm transition-colors hover:bg-blue-50 hover:text-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled}
        onClick={selectFiles}
        type="button"
      >
        <Upload className="size-4 shrink-0" aria-hidden="true" />
        <span className="flex flex-col gap-0.5">
          <span className="text-sm font-medium">{buttonText}</span>
          <span className="text-xs font-normal text-slate-500 group-hover:text-blue-600">
            Choose one or more files from JupyterLab
          </span>
        </span>
      </button>
    </div>
  );
}
