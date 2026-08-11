import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { RemoteServerId } from '../remoteServers';

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

function getRemoteServerOverride(): RemoteServerId | undefined {
  return useInvenioRDMUiStore.getState().remoteServerOverride;
}

function useCurrentTabID(): string {
  return useInvenioRDMUiStore(state => state.currentTab);
}

function useRemoteServerOverride(): RemoteServerId | undefined {
  return useInvenioRDMUiStore(state => state.remoteServerOverride);
}

function setCurrentTabID(currentTab: string): void {
  useInvenioRDMUiStore.setState({ currentTab });
}

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
