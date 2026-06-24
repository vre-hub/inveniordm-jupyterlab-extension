import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface IZenodoUiState {
  currentTab: string;
  sandboxOverride: boolean | undefined;
}


const useZenodoUiStore = create<IZenodoUiState>()(
  persist(
    () => ({
      currentTab: 'login' as string,
      sandboxOverride: undefined as boolean | undefined
    }),
    {
      name: 'zenodo-jupyterlab-store'
    }
  )
);

function getSandboxOverride(): boolean | undefined {
  return useZenodoUiStore.getState().sandboxOverride;
}

function useCurrentTabID(): string {
  return useZenodoUiStore(state => state.currentTab);
}

function useSandboxOverride(): boolean | undefined {
  return useZenodoUiStore(state => state.sandboxOverride);
}

function setCurrentTabID(currentTab: string): void {
  useZenodoUiStore.setState({ currentTab });
}

function setSandboxOverride(sandboxOverride: boolean | undefined): void {
  useZenodoUiStore.setState({ sandboxOverride });
}

export {
  getSandboxOverride,
  setCurrentTabID,
  setSandboxOverride,
  useCurrentTabID,
  useSandboxOverride
};
