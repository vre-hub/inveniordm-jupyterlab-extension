import React from 'react';

import {
  InvenioRDMPaginationParameters,
  InvenioRDMRecordData,
  InvenioRDMRecordSearchResponse
} from '../api_calls';

const DEFAULT_PAGE_SIZE = 10;

type FetchRecords = (
  pagination: InvenioRDMPaginationParameters
) => Promise<InvenioRDMRecordSearchResponse>;

export type PaginatedInvenioRDMRecords = {
  records: InvenioRDMRecordData[];
  total: number;
  page: number;
  pageSize: number;
  isLoading: boolean;
  error: string | null;
  loadPage: (page: number) => Promise<void>;
};

export function usePaginatedInvenioRDMRecords(
  fetchRecords: FetchRecords
): PaginatedInvenioRDMRecords {
  const [records, setRecords] = React.useState<InvenioRDMRecordData[]>([]);
  const [total, setTotal] = React.useState(0);
  const [page, setPage] = React.useState(1);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadPage = React.useCallback(
    async (requestedPage: number): Promise<void> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetchRecords({
          page: requestedPage,
          size: DEFAULT_PAGE_SIZE
        });
        const responseRecords = response.hits?.hits ?? [];

        setRecords(responseRecords);
        setTotal(response.hits?.total ?? responseRecords.length);
        setPage(requestedPage);
      } catch (reason) {
        setError(String(reason));
      } finally {
        setIsLoading(false);
      }
    },
    [fetchRecords]
  );

  return {
    records,
    total,
    page,
    pageSize: DEFAULT_PAGE_SIZE,
    isLoading,
    error,
    loadPage
  };
}
