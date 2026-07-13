import React from 'react';

import { listZenodoDepositions } from '../api_calls';
import { useServerSettings } from '../store';
import { DepositionUpload } from './DepositionUpload';
import { ZenodoResource, ZenodoResourceData } from './ZenodoResource';

export const ZenodoDepositions: React.FC = () => {
  const serverSettings = useServerSettings();
  const [depositions, setDepositions] = React.useState<
    ZenodoResourceData[] | { error: string } | null
  >(null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadDepositions = React.useCallback(async (): Promise<void> => {
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
  }, [serverSettings]);

  React.useEffect(() => {
    void loadDepositions();
  }, [loadDepositions]);

  return (
    <div>
      <h2>My Records</h2>
      {isLoading && <p>Loading...</p>}
      {Array.isArray(depositions)
        ? depositions.map(deposition => (
            <React.Fragment key={deposition.id}>
              <ZenodoResource resource={deposition} />
              <DepositionUpload
                depositionId={deposition.id}
                onDone={() => void loadDepositions()}
              />
            </React.Fragment>
          ))
        : depositions?.error}
    </div>
  );
};
