import { Store } from 'pullstate';

interface IZenodoState {
  isSandboxOverride: boolean;
}

export const ZenodoStore = new Store<IZenodoState>({
  isSandboxOverride: false
});

export function setIsSandboxOverride(isSandbox: boolean): void {
  ZenodoStore.update(state => {
    state.isSandboxOverride = isSandbox;
  });
}
