import React from 'react';

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
    <button disabled={disabled} onClick={selectFiles} type="button">
      {buttonText}
    </button>
  );
}
