import React from 'react';

import { listZenodoUserRecords } from '../api_calls';
import { useServerSettings } from '../store';
import { ZenodoResource, ZenodoResourceData } from './ZenodoResource';

export const ZenodoUserRecords: React.FC = () => {
  const serverSettings = useServerSettings();
  const [records, setRecords] = React.useState<
    ZenodoResourceData[] | { error: string } | null
  >(null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadRecords = React.useCallback(async (): Promise<void> => {
    setIsLoading(true);

    try {
      setRecords(
        (await listZenodoUserRecords(serverSettings)) as ZenodoResourceData[]
      );
    } catch (reason) {
      setRecords({ error: String(reason) });
    } finally {
      setIsLoading(false);
    }
  }, [serverSettings]);

  React.useEffect(() => {
    void loadRecords();
  }, [loadRecords]);

  return (
    <div>
      <h2>My Records</h2>
      {isLoading && <p>Loading...</p>}
      {Array.isArray(records)
        ? records.map(record => (
            <React.Fragment key={record.id}>
              <ZenodoResource resource={record} />
            </React.Fragment>
          ))
        : records?.error}
    </div>
  );
};
