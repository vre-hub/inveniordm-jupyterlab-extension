import React from 'react';
import { ServerConnection } from '@jupyterlab/services';

import { searchZenodoRecords } from '../api_calls';
import { ZenodoStore } from '../store';

interface IZenodoSearchProps {
  serverSettings: ServerConnection.ISettings;
}

export const ZenodoSearch: React.FC<IZenodoSearchProps> = ({
  serverSettings
}) => {
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<unknown>(null);
  const [isSearching, setIsSearching] = React.useState(false);
  const sandboxOverride = ZenodoStore.useState(state => state.sandboxOverride);

  const submitSearch = async (
    event: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    event.preventDefault();
    setIsSearching(true);

    try {
      setResults(
        await searchZenodoRecords(serverSettings, query, {
          sandbox: sandboxOverride
        })
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
      {results ? (
        <pre
          style={{
            maxHeight: '320px',
            maxWidth: '100%',
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}
        >
          {JSON.stringify(results, null, 2)}
        </pre>
      ) : null}
    </div>
  );
};
