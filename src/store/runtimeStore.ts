import { ServerConnection } from '@jupyterlab/services';
import { create } from 'zustand';

import type { InsertZenodoCellAction } from '../insertCell';

interface IZenodoRuntimeState {
  insertZenodoCell: ((action: InsertZenodoCellAction) => void) | undefined;
  pickDownloadDirectory: (() => Promise<string | null>) | undefined;
  pickUploadFiles: (() => Promise<string[] | null>) | undefined;
  serverSettings: unknown;
}

const useZenodoRuntimeStore = create<IZenodoRuntimeState>()(() => ({
  insertZenodoCell: undefined,
  pickDownloadDirectory: undefined,
  pickUploadFiles: undefined,
  serverSettings: undefined
}));

function setInsertZenodoCell(
  insertZenodoCell: (action: InsertZenodoCellAction) => void
): void {
  useZenodoRuntimeStore.setState({ insertZenodoCell });
}

function setServerSettings(serverSettings: ServerConnection.ISettings): void {
  useZenodoRuntimeStore.setState({ serverSettings });
}

function setPickDownloadDirectory(
  pickDownloadDirectory: () => Promise<string | null>
): void {
  useZenodoRuntimeStore.setState({ pickDownloadDirectory });
}

function setPickUploadFiles(
  pickUploadFiles: () => Promise<string[] | null>
): void {
  useZenodoRuntimeStore.setState({ pickUploadFiles });
}

function initializeZenodoStore(options: {
  insertZenodoCell: (action: InsertZenodoCellAction) => void;
  pickDownloadDirectory: () => Promise<string | null>;
  pickUploadFiles: () => Promise<string[] | null>;
  serverSettings: ServerConnection.ISettings;
}): void {
  setInsertZenodoCell(options.insertZenodoCell);
  setPickDownloadDirectory(options.pickDownloadDirectory);
  setPickUploadFiles(options.pickUploadFiles);
  setServerSettings(options.serverSettings);
}

function useServerSettings(): ServerConnection.ISettings {
  const serverSettings = useZenodoRuntimeStore(state => state.serverSettings);

  if (!serverSettings) {
    throw new Error('Zenodo server settings have not been initialized.');
  }

  return serverSettings as ServerConnection.ISettings;
}

function useInsertZenodoCell(): (action: InsertZenodoCellAction) => void {
  const insertZenodoCell = useZenodoRuntimeStore(
    state => state.insertZenodoCell
  );

  if (!insertZenodoCell) {
    throw new Error('Zenodo cell insertion has not been initialized.');
  }

  return insertZenodoCell;
}

function usePickDownloadDirectory(): () => Promise<string | null> {
  const pickDownloadDirectory = useZenodoRuntimeStore(
    state => state.pickDownloadDirectory
  );

  if (!pickDownloadDirectory) {
    throw new Error('Zenodo directory picker has not been initialized.');
  }

  return pickDownloadDirectory;
}

function usePickUploadFiles(): () => Promise<string[] | null> {
  const pickUploadFiles = useZenodoRuntimeStore(state => state.pickUploadFiles);

  if (!pickUploadFiles) {
    throw new Error('Zenodo file picker has not been initialized.');
  }

  return pickUploadFiles;
}

export {
  initializeZenodoStore,
  setInsertZenodoCell,
  setPickDownloadDirectory,
  setPickUploadFiles,
  setServerSettings,
  useInsertZenodoCell,
  usePickDownloadDirectory,
  usePickUploadFiles,
  useServerSettings
};
