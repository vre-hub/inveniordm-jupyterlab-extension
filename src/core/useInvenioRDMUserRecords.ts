import React from 'react';
import { InvenioRDMRecordData, listInvenioRDMUserRecords } from '../api_calls';
import { useServerSettings } from '../store';

export function useInvenioRDMUserRecords() {
  const serverSettings = useServerSettings();
  const [records, setRecords] = React.useState<
    InvenioRDMRecordData[] | { error: string } | null
  >(null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadRecords = React.useCallback(async (): Promise<void> => {
    setIsLoading(true);

    try {
      const response = await listInvenioRDMUserRecords(serverSettings, {
        page: 1,
        size: 10
      });
      setRecords(response.hits?.hits ?? []);
    } catch (reason) {
      setRecords({ error: String(reason) });
    } finally {
      setIsLoading(false);
    }
  }, [serverSettings]);

  React.useEffect(() => {
    void loadRecords();
  }, [loadRecords]);

  return { records, isLoading };
}
