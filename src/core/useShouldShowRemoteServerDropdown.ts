import { useRemoteServers } from './useRemoteServers';

export function useShouldShowRemoteServerDropdownForLogin(): boolean {
  const remoteServers = useRemoteServers();
  return remoteServers.length > 1;
}
