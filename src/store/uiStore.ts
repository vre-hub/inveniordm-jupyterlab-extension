import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface IZenodoUiState {
  sandboxOverride: boolean | undefined;
}

const useZenodoUiStore = create<IZenodoUiState>()(
  persist(
    () => ({
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

function useSandboxOverride(): boolean | undefined {
  return useZenodoUiStore(state => state.sandboxOverride);
}

function setSandboxOverride(sandboxOverride: boolean | undefined): void {
  useZenodoUiStore.setState({ sandboxOverride });
}

export { getSandboxOverride, setSandboxOverride, useSandboxOverride };
