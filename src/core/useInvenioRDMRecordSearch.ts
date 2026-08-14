import React from 'react';
import { useServerSettings } from '../store';
import {
  InvenioRDMPaginationParameters,
  searchInvenioRDMRecords
} from '../api_calls';
import { usePaginatedInvenioRDMRecords } from './usePaginatedInvenioRDMRecords';

/** Provides query state and paginated results for public record search. */
export function useInvenioRDMRecordSearch() {
  const serverSettings = useServerSettings();
  const submittedQuery = React.useRef<string>();
  const fetchRecords = React.useCallback(
    async (pagination: InvenioRDMPaginationParameters) => {
      if (submittedQuery.current === undefined) {
        throw new Error('Search records before loading another page');
      }

      return await searchInvenioRDMRecords(
        serverSettings,
        submittedQuery.current,
        pagination
      );
    },
    [serverSettings]
  );
  const paginatedRecords = usePaginatedInvenioRDMRecords(fetchRecords);

  const search = React.useCallback(
    async (query: string): Promise<void> => {
      submittedQuery.current = query;
      await paginatedRecords.loadPage(1);
    },
    [paginatedRecords.loadPage]
  );

  return { ...paginatedRecords, search };
}
