import React from 'react';

import { usePickUploadFiles } from '../store';

type PickFilesButtonProps = {
  buttonText: string;
  onFilesSelected: (files: string[]) => void;
};

export function PickFilesButton({
  buttonText,
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
    <button onClick={selectFiles} type="button">
      {buttonText}
    </button>
  );
}
