import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { RemoteServerId } from '../remoteServers';

interface IZenodoUiState {
  currentTab: string;
  remoteServerOverride: RemoteServerId | undefined;
}

const useZenodoUiStore = create<IZenodoUiState>()(
  persist(
    () => ({
      currentTab: 'login' as string,
      remoteServerOverride: undefined as RemoteServerId | undefined
    }),
    {
      name: 'zenodo-jupyterlab-store'
    }
  )
);

function getRemoteServerOverride(): RemoteServerId | undefined {
  return useZenodoUiStore.getState().remoteServerOverride;
}

function useCurrentTabID(): string {
  return useZenodoUiStore(state => state.currentTab);
}

function useRemoteServerOverride(): RemoteServerId | undefined {
  return useZenodoUiStore(state => state.remoteServerOverride);
}

function setCurrentTabID(currentTab: string): void {
  useZenodoUiStore.setState({ currentTab });
}

function setRemoteServerOverride(
  remoteServerOverride: RemoteServerId | undefined
): void {
  useZenodoUiStore.setState({ remoteServerOverride });
}

export {
  getRemoteServerOverride,
  setCurrentTabID,
  setRemoteServerOverride,
  useCurrentTabID,
  useRemoteServerOverride
};
