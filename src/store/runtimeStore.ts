import { ServerConnection } from '@jupyterlab/services';
import { create } from 'zustand';

import type { InsertInvenioRDMCellAction } from '../jupyterlab_interactions';

interface IInvenioRDMRuntimeState {
  insertInvenioRDMCell: ((action: InsertInvenioRDMCellAction) => void) | undefined;
  pickDownloadDirectory: (() => Promise<string | null>) | undefined;
  pickUploadFiles: (() => Promise<string[] | null>) | undefined;
  serverSettings: unknown;
}

const useInvenioRDMRuntimeStore = create<IInvenioRDMRuntimeState>()(() => ({
  insertInvenioRDMCell: undefined,
  pickDownloadDirectory: undefined,
  pickUploadFiles: undefined,
  serverSettings: undefined
}));

function setInsertInvenioRDMCell(
  insertInvenioRDMCell: (action: InsertInvenioRDMCellAction) => void
): void {
  useInvenioRDMRuntimeStore.setState({ insertInvenioRDMCell });
}

function setServerSettings(serverSettings: ServerConnection.ISettings): void {
  useInvenioRDMRuntimeStore.setState({ serverSettings });
}

function setPickDownloadDirectory(
  pickDownloadDirectory: () => Promise<string | null>
): void {
  useInvenioRDMRuntimeStore.setState({ pickDownloadDirectory });
}

function setPickUploadFiles(
  pickUploadFiles: () => Promise<string[] | null>
): void {
  useInvenioRDMRuntimeStore.setState({ pickUploadFiles });
}

function initializeInvenioRDMStore(options: {
  insertInvenioRDMCell: (action: InsertInvenioRDMCellAction) => void;
  pickDownloadDirectory: () => Promise<string | null>;
  pickUploadFiles: () => Promise<string[] | null>;
  serverSettings: ServerConnection.ISettings;
}): void {
  setInsertInvenioRDMCell(options.insertInvenioRDMCell);
  setPickDownloadDirectory(options.pickDownloadDirectory);
  setPickUploadFiles(options.pickUploadFiles);
  setServerSettings(options.serverSettings);
}

function useServerSettings(): ServerConnection.ISettings {
  const serverSettings = useInvenioRDMRuntimeStore(state => state.serverSettings);

  if (!serverSettings) {
    throw new Error('InvenioRDM server settings have not been initialized.');
  }

  return serverSettings as ServerConnection.ISettings;
}

function useInsertInvenioRDMCell(): (action: InsertInvenioRDMCellAction) => void {
  const insertInvenioRDMCell = useInvenioRDMRuntimeStore(
    state => state.insertInvenioRDMCell
  );

  if (!insertInvenioRDMCell) {
    throw new Error('InvenioRDM cell insertion has not been initialized.');
  }

  return insertInvenioRDMCell;
}

function usePickDownloadDirectory(): () => Promise<string | null> {
  const pickDownloadDirectory = useInvenioRDMRuntimeStore(
    state => state.pickDownloadDirectory
  );

  if (!pickDownloadDirectory) {
    throw new Error('InvenioRDM directory picker has not been initialized.');
  }

  return pickDownloadDirectory;
}

function usePickUploadFiles(): () => Promise<string[] | null> {
  const pickUploadFiles = useInvenioRDMRuntimeStore(state => state.pickUploadFiles);

  if (!pickUploadFiles) {
    throw new Error('InvenioRDM file picker has not been initialized.');
  }

  return pickUploadFiles;
}

export {
  initializeInvenioRDMStore,
  setInsertInvenioRDMCell,
  setPickDownloadDirectory,
  setPickUploadFiles,
  setServerSettings,
  useInsertInvenioRDMCell,
  usePickDownloadDirectory,
  usePickUploadFiles,
  useServerSettings
};
