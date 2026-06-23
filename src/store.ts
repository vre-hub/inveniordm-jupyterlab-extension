import { ServerConnection } from '@jupyterlab/services';
import { Store } from 'pullstate';

interface IZenodoState {
  sandboxOverride: boolean | undefined;
  serverSettings: unknown;
}

export const ZenodoStore = new Store<IZenodoState>({
  sandboxOverride: undefined,
  serverSettings: undefined
});

export function setSandboxOverride(sandboxOverride: boolean | undefined): void {
  ZenodoStore.update(state => {
    state.sandboxOverride = sandboxOverride;
  });
}

export function initializeZenodoStore(options: {
  serverSettings: ServerConnection.ISettings;
}): void {
  ZenodoStore.update(state => {
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
