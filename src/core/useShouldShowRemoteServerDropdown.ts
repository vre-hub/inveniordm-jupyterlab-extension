import { useRemoteServers } from './useRemoteServers';

/** Reports whether login should offer a repository selector. */
export function useShouldShowRemoteServerDropdownForLogin(): boolean {
  const remoteServers = useRemoteServers();
  return remoteServers.length > 1;
}
