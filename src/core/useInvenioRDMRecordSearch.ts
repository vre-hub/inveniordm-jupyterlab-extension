import React from 'react';
import { useServerSettings } from '../store';
import { InvenioRDMRecordData, searchInvenioRDMRecords } from '../api_calls';

type InvenioRDMRecordSearchResponse = {
  hits?: {
    hits?: InvenioRDMRecordData[];
  };
};

export function useInvenioRDMRecordSearch() {
  const serverSettings = useServerSettings();
  const [results, setResults] = React.useState<
    InvenioRDMRecordSearchResponse | { error: string } | null
  >(null);
  const [isSearching, setIsSearching] = React.useState(false);
  const error = results && 'error' in results ? results.error : null;
  const hits =
    results && !('error' in results) ? (results.hits?.hits ?? []) : [];

  const search = async (query: string): Promise<void> => {
    setIsSearching(true);

    try {
      setResults(
        (await searchInvenioRDMRecords(
          serverSettings,
          query
        )) as InvenioRDMRecordSearchResponse
      );
    } catch (reason) {
      setResults({ error: String(reason) });
    } finally {
      setIsSearching(false);
    }
  };

  return { isSearching, error, hits, search };
}
