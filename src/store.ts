import { ServerConnection } from '@jupyterlab/services';
import { Store } from 'pullstate';

import type { InsertZenodoCellAction } from './insertCell';

interface IZenodoState {
  insertZenodoCell: ((action: InsertZenodoCellAction) => void) | undefined;
  sandboxOverride: boolean | undefined;
  serverSettings: unknown;
}

export const ZenodoStore = new Store<IZenodoState>({
  insertZenodoCell: undefined,
  sandboxOverride: undefined,
  serverSettings: undefined
});

export function setSandboxOverride(sandboxOverride: boolean | undefined): void {
  ZenodoStore.update(state => {
    state.sandboxOverride = sandboxOverride;
  });
}

export function initializeZenodoStore(options: {
  insertZenodoCell: (action: InsertZenodoCellAction) => void;
  serverSettings: ServerConnection.ISettings;
}): void {
  ZenodoStore.update(state => {
    state.insertZenodoCell = options.insertZenodoCell;
    state.serverSettings = options.serverSettings;
  });
}

export function useServerSettings(): ServerConnection.ISettings {
  const serverSettings = ZenodoStore.useState(state => state.serverSettings);

  if (!serverSettings) {
    throw new Error('Zenodo server settings have not been initialized.');
  }

  return serverSettings as ServerConnection.ISettings;
}

export function useInsertZenodoCell(): (
  action: InsertZenodoCellAction
) => void {
  const insertZenodoCell = ZenodoStore.useState(state => state.insertZenodoCell);

  if (!insertZenodoCell) {
    throw new Error('Zenodo cell insertion has not been initialized.');
  }

  return insertZenodoCell;
}
