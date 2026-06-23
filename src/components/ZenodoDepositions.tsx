import React from 'react';
import { ServerConnection } from '@jupyterlab/services';

import { listZenodoDepositions } from '../api_calls';
import { ZenodoStore } from '../store';
import { ZenodoResource, ZenodoResourceData } from './ZenodoResource';

interface IZenodoDepositionsProps {
  serverSettings: ServerConnection.ISettings;
}

export const ZenodoDepositions: React.FC<IZenodoDepositionsProps> = ({
  serverSettings
}) => {
  const [depositions, setDepositions] = React.useState<
    ZenodoResourceData[] | { error: string } | null
  >(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const sandboxOverride = ZenodoStore.useState(state => state.sandboxOverride);

  const loadDepositions = async (): Promise<void> => {
    setIsLoading(true);

    try {
      setDepositions(
        (await listZenodoDepositions(serverSettings, {
          sandbox: sandboxOverride
        })) as ZenodoResourceData[]
      );
    } catch (reason) {
      setDepositions({ error: String(reason) });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <button disabled={isLoading} onClick={loadDepositions} type="button">
        {isLoading ? 'Loading...' : 'Load depositions'}
      </button>
      {Array.isArray(depositions)
        ? depositions.map(deposition => (
            <ZenodoResource resource={deposition} key={deposition.id} />
          ))
        : depositions?.error}
    </div>
  );
};
