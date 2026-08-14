import { ServerConnection } from '@jupyterlab/services';
import { create } from 'zustand';

import type { InsertInvenioRDMCellAction } from '../jupyterlab_interactions';

/** JupyterLab services supplied to the React application at startup. */
interface IInvenioRDMRuntimeState {
  insertInvenioRDMCell:
    ((action: InsertInvenioRDMCellAction) => void) | undefined;
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

/** Registers the notebook-cell integration used by React components. */
function setInsertInvenioRDMCell(
  insertInvenioRDMCell: (action: InsertInvenioRDMCellAction) => void
): void {
  useInvenioRDMRuntimeStore.setState({ insertInvenioRDMCell });
}

/** Registers the active Jupyter server connection settings. */
function setServerSettings(serverSettings: ServerConnection.ISettings): void {
  useInvenioRDMRuntimeStore.setState({ serverSettings });
}

/** Registers the JupyterLab directory picker. */
function setPickDownloadDirectory(
  pickDownloadDirectory: () => Promise<string | null>
): void {
  useInvenioRDMRuntimeStore.setState({ pickDownloadDirectory });
}

/** Registers the JupyterLab file picker. */
function setPickUploadFiles(
  pickUploadFiles: () => Promise<string[] | null>
): void {
  useInvenioRDMRuntimeStore.setState({ pickUploadFiles });
}

/** Initializes the runtime services required by the extension UI. */
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

/** Returns the active Jupyter server connection settings. */
function useServerSettings(): ServerConnection.ISettings {
  const serverSettings = useInvenioRDMRuntimeStore(
    state => state.serverSettings
  );

  if (!serverSettings) {
    throw new Error('InvenioRDM server settings have not been initialized.');
  }

  return serverSettings as ServerConnection.ISettings;
}

/** Returns the registered notebook-cell integration. */
function useInsertInvenioRDMCell(): (
  action: InsertInvenioRDMCellAction
) => void {
  const insertInvenioRDMCell = useInvenioRDMRuntimeStore(
    state => state.insertInvenioRDMCell
  );

  if (!insertInvenioRDMCell) {
    throw new Error('InvenioRDM cell insertion has not been initialized.');
  }

  return insertInvenioRDMCell;
}

/** Returns the registered JupyterLab directory picker. */
function usePickDownloadDirectory(): () => Promise<string | null> {
  const pickDownloadDirectory = useInvenioRDMRuntimeStore(
    state => state.pickDownloadDirectory
  );

  if (!pickDownloadDirectory) {
    throw new Error('InvenioRDM directory picker has not been initialized.');
  }

  return pickDownloadDirectory;
}

/** Returns the registered JupyterLab file picker. */
function usePickUploadFiles(): () => Promise<string[] | null> {
  const pickUploadFiles = useInvenioRDMRuntimeStore(
    state => state.pickUploadFiles
  );

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
