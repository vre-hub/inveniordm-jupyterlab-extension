import { ServerConnection } from '@jupyterlab/services';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import type { InsertZenodoCellAction } from './insertCell';

interface IZenodoState {
  insertZenodoCell: ((action: InsertZenodoCellAction) => void) | undefined;
  sandboxOverride: boolean | undefined;
  serverSettings: unknown;
}

type IZenodoPersistedState = Omit<
  IZenodoState,
  'insertZenodoCell' | 'serverSettings'
>;

const useZenodoStore = create<IZenodoState>()(
  persist<IZenodoState, [], [], IZenodoPersistedState>(
    () => ({
      insertZenodoCell: undefined,
      sandboxOverride: undefined,
      serverSettings: undefined
    }),
    {
      name: 'zenodo-jupyterlab-store',
      partialize: state => {
        const { insertZenodoCell, serverSettings, ...persistedState } = state;
        return persistedState;
      }
    }
  )
);

function getSandboxOverride(): boolean | undefined {
  return useZenodoStore.getState().sandboxOverride;
}

function useSandboxOverride(): boolean | undefined {
  return useZenodoStore(state => state.sandboxOverride);
}

function setSandboxOverride(sandboxOverride: boolean | undefined): void {
  useZenodoStore.setState({ sandboxOverride });
}

function setInsertZenodoCell(
  insertZenodoCell: (action: InsertZenodoCellAction) => void
): void {
  useZenodoStore.setState({ insertZenodoCell });
}

function setServerSettings(serverSettings: ServerConnection.ISettings): void {
  useZenodoStore.setState({ serverSettings });
}

function initializeZenodoStore(options: {
  insertZenodoCell: (action: InsertZenodoCellAction) => void;
  serverSettings: ServerConnection.ISettings;
}): void {
  setInsertZenodoCell(options.insertZenodoCell);
  setServerSettings(options.serverSettings);
}

function useServerSettings(): ServerConnection.ISettings {
  const serverSettings = useZenodoStore(state => state.serverSettings);

  if (!serverSettings) {
    throw new Error('Zenodo server settings have not been initialized.');
  }

  return serverSettings as ServerConnection.ISettings;
}

function useInsertZenodoCell(): (
  action: InsertZenodoCellAction
) => void {
  const insertZenodoCell = useZenodoStore(state => state.insertZenodoCell);

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
