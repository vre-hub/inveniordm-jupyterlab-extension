import { ServerConnection } from '@jupyterlab/services';
import { create } from 'zustand';

import type { InsertZenodoCellAction } from '../insertCell';

interface IZenodoRuntimeState {
  insertZenodoCell: ((action: InsertZenodoCellAction) => void) | undefined;
  serverSettings: unknown;
}

const useZenodoRuntimeStore = create<IZenodoRuntimeState>()(() => ({
  insertZenodoCell: undefined,
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

function initializeZenodoStore(options: {
  insertZenodoCell: (action: InsertZenodoCellAction) => void;
  serverSettings: ServerConnection.ISettings;
}): void {
  setInsertZenodoCell(options.insertZenodoCell);
  setServerSettings(options.serverSettings);
}

function useServerSettings(): ServerConnection.ISettings {
  const serverSettings = useZenodoRuntimeStore(state => state.serverSettings);

  if (!serverSettings) {
    throw new Error('Zenodo server settings have not been initialized.');
  }

  return serverSettings as ServerConnection.ISettings;
}

function useInsertZenodoCell(): (
  action: InsertZenodoCellAction
) => void {
  const insertZenodoCell = useZenodoRuntimeStore(
    state => state.insertZenodoCell
  );

  if (!insertZenodoCell) {
    throw new Error('Zenodo cell insertion has not been initialized.');
  }

  return insertZenodoCell;
}

export {
  initializeZenodoStore,
  setInsertZenodoCell,
  setServerSettings,
  useInsertZenodoCell,
  useServerSettings
};
