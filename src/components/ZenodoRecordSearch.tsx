import React from 'react';

import { ZenodoVersionedRecord } from './ZenodoVersionedRecord';
import { ZenodoRecordRenderer } from './ZenodoRecordRenderer';
import { useZenodoRecordSearch } from '../core/useZenodoRecordSearch';

export const ZenodoRecordSearch: React.FC = () => {
  const [query, setQuery] = React.useState('');

  const { isSearching, error, hits, search } = useZenodoRecordSearch();

  const submitSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    search(query);
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
          initialRecordIdentifier={{
            record_id: result.id,
            record_status: 'published'
          }}
          initialRecordValue={result}
          include_drafts_in_version_dropdown={false}
          renderRecord={zenodoRecordRendererProps => (
            <ZenodoRecordRenderer {...zenodoRecordRendererProps} />
          )}
        />
      ))}
    </div>
  );
};
