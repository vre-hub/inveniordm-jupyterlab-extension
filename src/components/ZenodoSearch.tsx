import React from 'react';
import { ServerConnection } from '@jupyterlab/services';

import { searchZenodoRecords } from '../api_calls';
import { ZenodoStore } from '../store';
import { ZenodoResource, ZenodoResourceData } from './ZenodoResource';

interface IZenodoSearchProps {
  serverSettings: ServerConnection.ISettings;
}

type ZenodoSearchResults = {
  hits?: {
    hits?: ZenodoResourceData[];
  };
};

export const ZenodoSearch: React.FC<IZenodoSearchProps> = ({
  serverSettings
}) => {
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<
    ZenodoSearchResults | { error: string } | null
  >(null);
  const [isSearching, setIsSearching] = React.useState(false);
  const sandboxOverride = ZenodoStore.useState(state => state.sandboxOverride);
  const error = results && 'error' in results ? results.error : null;
  const hits = results && !('error' in results) ? results.hits?.hits ?? [] : [];

  const submitSearch = async (
    event: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    event.preventDefault();
    setIsSearching(true);

    try {
      setResults(
        (await searchZenodoRecords(serverSettings, query, {
          sandbox: sandboxOverride
        })) as ZenodoSearchResults
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
        <ZenodoResource resource={result} key={result.id} />
      ))}
    </div>
  );
};
