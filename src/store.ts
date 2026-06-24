import { ServerConnection } from '@jupyterlab/services';
import { Store } from 'pullstate';

import type { InsertZenodoCellAction } from './insertCell';

interface IZenodoState {
  insertZenodoCell: ((action: InsertZenodoCellAction) => void) | undefined;
  sandboxOverride: boolean | undefined;
  serverSettings: unknown;
}

const ZenodoStore = new Store<IZenodoState>({
  insertZenodoCell: undefined,
  sandboxOverride: undefined,
  serverSettings: undefined
});

function getSandboxOverride(): boolean | undefined {
  return ZenodoStore.getRawState().sandboxOverride;
}

function useSandboxOverride(): boolean | undefined {
  return ZenodoStore.useState(state => state.sandboxOverride);
}

function setSandboxOverride(sandboxOverride: boolean | undefined): void {
  ZenodoStore.update(state => {
    state.sandboxOverride = sandboxOverride;
  });
}

function setInsertZenodoCell(
  insertZenodoCell: (action: InsertZenodoCellAction) => void
): void {
  ZenodoStore.update(state => {
    state.insertZenodoCell = insertZenodoCell;
  });
}

function setServerSettings(
  serverSettings: ServerConnection.ISettings
): void {
  ZenodoStore.update(state => {
    state.serverSettings = serverSettings;
  });
}

function initializeZenodoStore(options: {
  insertZenodoCell: (action: InsertZenodoCellAction) => void;
  serverSettings: ServerConnection.ISettings;
}): void {
  setInsertZenodoCell(options.insertZenodoCell);
  setServerSettings(options.serverSettings);
}

function useServerSettings(): ServerConnection.ISettings {
  const serverSettings = ZenodoStore.useState(state => state.serverSettings);

  if (!serverSettings) {
    throw new Error('Zenodo server settings have not been initialized.');
  }

  return serverSettings as ServerConnection.ISettings;
}

function useInsertZenodoCell(): (
  action: InsertZenodoCellAction
) => void {
  const insertZenodoCell = ZenodoStore.useState(state => state.insertZenodoCell);

  if (!insertZenodoCell) {
    throw new Error('Zenodo cell insertion has not been initialized.');
  }

  return insertZenodoCell;
}

// export hooks
export {
  useInsertZenodoCell,
  useSandboxOverride,
  useServerSettings
};

// export getters and setters
export {
  setInsertZenodoCell,
  getSandboxOverride,
  setSandboxOverride,
  setServerSettings
};

// export initialize function
export { initializeZenodoStore };