import React from 'react';
import {
  InvenioRDMPaginationParameters,
  listInvenioRDMUserRecords
} from '../api_calls';
import { useServerSettings } from '../store';
import { usePaginatedInvenioRDMRecords } from './usePaginatedInvenioRDMRecords';

export function useInvenioRDMUserRecords() {
  const serverSettings = useServerSettings();
  const fetchRecords = React.useCallback(
    async (pagination: InvenioRDMPaginationParameters) =>
      await listInvenioRDMUserRecords(serverSettings, pagination),
    [serverSettings]
  );
  const paginatedRecords = usePaginatedInvenioRDMRecords(fetchRecords);

  React.useEffect(() => {
    void paginatedRecords.loadPage(1);
  }, [paginatedRecords.loadPage]);

  return paginatedRecords;
}
