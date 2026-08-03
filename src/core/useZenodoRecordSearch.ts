import React from 'react';
import { useServerSettings } from '../store';
import { ZenodoRecordData, searchZenodoRecords } from '../api_calls';

type ZenodoRecordSearchResponse = {
  hits?: {
    hits?: ZenodoRecordData[];
  };
};

export function useZenodoRecordSearch() {
  const serverSettings = useServerSettings();
  const [results, setResults] = React.useState<
    ZenodoRecordSearchResponse | { error: string } | null
  >(null);
  const [isSearching, setIsSearching] = React.useState(false);
  const error = results && 'error' in results ? results.error : null;
  const hits =
    results && !('error' in results) ? (results.hits?.hits ?? []) : [];

  const search = async (query: string): Promise<void> => {
    setIsSearching(true);

    try {
      setResults(
        (await searchZenodoRecords(
          serverSettings,
          query
        )) as ZenodoRecordSearchResponse
      );
    } catch (reason) {
      setResults({ error: String(reason) });
    } finally {
      setIsSearching(false);
    }
  };

  return { isSearching, error, hits, search };
}
