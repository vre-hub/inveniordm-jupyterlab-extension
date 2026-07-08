import React from "react";
import { usePickDownloadDirectory } from "../store";

/**
 * A button that opens the jupyterlab file picker to select a directory.
 */
export function PickDirectoryButton({
    onDirectorySelected,
    buttonText
}: {
    onDirectorySelected: (directory: string) => void
    buttonText: string
}): JSX.Element {
  const pickDownloadDirectory = usePickDownloadDirectory();

  const selectDownloadDirectory = async (): Promise<void> => {
    const directory = await pickDownloadDirectory();

    if (!directory) {
      return;
    }

    onDirectorySelected(directory);
  };

  return (
    <>
      <button onClick={selectDownloadDirectory} type="button">
        {buttonText}
      </button>
    </>
  );
}
