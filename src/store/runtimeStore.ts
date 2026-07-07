import { ServerConnection } from '@jupyterlab/services';
import { create } from 'zustand';

import type { InsertZenodoCellAction } from '../insertCell';

interface IZenodoRuntimeState {
  insertZenodoCell: ((action: InsertZenodoCellAction) => void) | undefined;
  pickDownloadDirectory: (() => Promise<string | null>) | undefined;
  serverSettings: unknown;
}

const useZenodoRuntimeStore = create<IZenodoRuntimeState>()(() => ({
  insertZenodoCell: undefined,
  pickDownloadDirectory: undefined,
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

function initializeZenodoStore(options: {
  insertZenodoCell: (action: InsertZenodoCellAction) => void;
  pickDownloadDirectory: () => Promise<string | null>;
  serverSettings: ServerConnection.ISettings;
}): void {
  setInsertZenodoCell(options.insertZenodoCell);
  setPickDownloadDirectory(options.pickDownloadDirectory);
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

export {
  initializeZenodoStore,
  setInsertZenodoCell,
  setPickDownloadDirectory,
  setServerSettings,
  useInsertZenodoCell,
  usePickDownloadDirectory,
  useServerSettings
};
