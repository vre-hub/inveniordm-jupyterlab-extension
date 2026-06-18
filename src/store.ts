import { Store } from 'pullstate';

interface IZenodoState {
  sandboxOverride: boolean | undefined;
}

export const ZenodoStore = new Store<IZenodoState>({
  sandboxOverride: undefined
});

export function setSandboxOverride(sandboxOverride: boolean | undefined): void {
  ZenodoStore.update(state => {
    state.sandboxOverride = sandboxOverride;
  });
}
