import React from 'react';

import { listZenodoDepositions } from '../api_calls';
import { useServerSettings } from '../store';
import { ZenodoResource, ZenodoResourceData } from './ZenodoResource';

export const ZenodoDepositions: React.FC = () => {
  const serverSettings = useServerSettings();
  const [depositions, setDepositions] = React.useState<
    ZenodoResourceData[] | { error: string } | null
  >(null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadDepositions = async (): Promise<void> => {
    setIsLoading(true);

    try {
      setDepositions(
        (await listZenodoDepositions(serverSettings)) as ZenodoResourceData[]
      );
    } catch (reason) {
      setDepositions({ error: String(reason) });
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    loadDepositions();
  }, [serverSettings]);

  return (
    <div>
      <h2>My Records</h2>
      {isLoading && <p>Loading...</p>}
      {Array.isArray(depositions)
        ? depositions.map(deposition => (
            <ZenodoResource resource={deposition} key={deposition.id} />
          ))
        : depositions?.error}
    </div>
  );
};
