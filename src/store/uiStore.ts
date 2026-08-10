import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import type { ZenodoRecordIdentifier } from '../api_calls';
import { RemoteServerId } from '../remoteServers';

interface IZenodoUiState {
  currentTab: string;
  remoteServerOverride: RemoteServerId | undefined;
  selectedUserRecordIdentifier: ZenodoRecordIdentifier | undefined;
}

const useZenodoUiStore = create<IZenodoUiState>()(
  persist(
    () => ({
      currentTab: 'login' as string,
      remoteServerOverride: undefined as RemoteServerId | undefined,
      selectedUserRecordIdentifier: undefined as
        ZenodoRecordIdentifier | undefined
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

function useSelectedUserRecordIdentifier(): ZenodoRecordIdentifier | undefined {
  return useZenodoUiStore(state => state.selectedUserRecordIdentifier);
}

function setCurrentTabID(currentTab: string): void {
  useZenodoUiStore.setState({ currentTab });
}

function setRemoteServerOverride(
  remoteServerOverride: RemoteServerId | undefined
): void {
  useZenodoUiStore.setState({ remoteServerOverride });
}

function setSelectedUserRecordIdentifier(
  selectedUserRecordIdentifier: ZenodoRecordIdentifier | undefined
): void {
  useZenodoUiStore.setState({ selectedUserRecordIdentifier });
}

export {
  getRemoteServerOverride,
  setCurrentTabID,
  setRemoteServerOverride,
  setSelectedUserRecordIdentifier,
  useCurrentTabID,
  useRemoteServerOverride,
  useSelectedUserRecordIdentifier
};
