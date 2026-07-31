import React from 'react';

import {
  getZenodoRecordVariant,
  searchZenodoRecords,
  ZenodoRecordData
} from '../api_calls';
import { useServerSettings } from '../store';
import { ZenodoVersionedRecord } from './ZenodoVersionedRecord';
import { ZenodoRecordDetails } from './ZenodoRecordDetails';

type ZenodoRecordSearchResponse = {
  hits?: {
    hits?: ZenodoRecordData[];
  };
};

export const ZenodoRecordSearch: React.FC = () => {
  const serverSettings = useServerSettings();
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<
    ZenodoRecordSearchResponse | { error: string } | null
  >(null);
  const [isSearching, setIsSearching] = React.useState(false);
  const error = results && 'error' in results ? results.error : null;
  const hits =
    results && !('error' in results) ? (results.hits?.hits ?? []) : [];

  const submitSearch = async (
    event: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    event.preventDefault();
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

  return (
    <div>
      <form onSubmit={submitSearch}>
        <input
          aria-label="Search Zenodo"
          onChange={event => setQuery(event.target.value)}
          placeholder="Search Zenodo"
          type="search"
          value={query}
        />
        <button disabled={isSearching} type="submit">
          {isSearching ? 'Searching...' : 'Search'}
        </button>
      </form>
      {error}
      {hits.map(result => (
        <ZenodoVersionedRecord
          key={result.id}
          initialRecordId={result.id}
          initialRecordValue={result}
          include_drafts_in_version_dropdown={false}
          fetchRecord={async (id: string): Promise<ZenodoRecordData> => {
            return await getZenodoRecordVariant(serverSettings, {
              record_id: id,
              record_status: 'published'
            });
          }}
          renderRecord={record => (
            <ZenodoRecordDetails record={record} editable={false} />
          )}
        />
      ))}
    </div>
  );
};
