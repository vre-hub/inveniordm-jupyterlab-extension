import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { RemoteServerId } from '../remoteServers';

/** Persisted choices that control the extension's user interface. */
interface IInvenioRDMUiState {
  currentTab: string;
  remoteServerOverride: RemoteServerId | undefined;
}

const useInvenioRDMUiStore = create<IInvenioRDMUiState>()(
  persist(
    () => ({
      currentTab: 'login' as string,
      remoteServerOverride: undefined as RemoteServerId | undefined
    }),
    {
      name: 'inveniordm-jupyterlab-store'
    }
  )
);

/** Returns the selected server override outside React. */
function getRemoteServerOverride(): RemoteServerId | undefined {
  return useInvenioRDMUiStore.getState().remoteServerOverride;
}

/** Returns the identifier of the selected sidebar tab. */
function useCurrentTabID(): string {
  return useInvenioRDMUiStore(state => state.currentTab);
}

/** Returns the user-selected server override. */
function useRemoteServerOverride(): RemoteServerId | undefined {
  return useInvenioRDMUiStore(state => state.remoteServerOverride);
}

/** Selects the active sidebar tab. */
function setCurrentTabID(currentTab: string): void {
  useInvenioRDMUiStore.setState({ currentTab });
}

/** Selects a server override or restores the configured default. */
function setRemoteServerOverride(
  remoteServerOverride: RemoteServerId | undefined
): void {
  useInvenioRDMUiStore.setState({ remoteServerOverride });
}

export {
  getRemoteServerOverride,
  setCurrentTabID,
  setRemoteServerOverride,
  useCurrentTabID,
  useRemoteServerOverride
};
