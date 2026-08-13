import React from 'react';
import { LoaderCircle, Search } from 'lucide-react';

import {
  InvenioRDMRecordPreview,
  InvenioRDMRecordRenderer
} from './InvenioRDMRecordRenderer';
import { InvenioRDMRecordList } from './InvenioRDMRecordList';
import { useCurrentRemoteServer, useInvenioRDMRecordSearch } from '../core';
import { ErrorPanel } from './ErrorPanel';

export const InvenioRDMRecordSearch: React.FC = () => {
  const [query, setQuery] = React.useState('');
  const { remoteServer } = useCurrentRemoteServer();
  const remoteName = remoteServer?.display_name ?? 'remote repository';

  const {
    isLoading: isSearching,
    error,
    records,
    search
  } = useInvenioRDMRecordSearch();

  const submitSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    search(query);
  };

  return (
    <div>
      <form className="mb-3 flex w-full min-w-0 gap-2" onSubmit={submitSearch}>
        <div className="relative min-w-0 flex-1">
          <Search
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted"
          />
          <input
            aria-label={`Search ${remoteName}`}
            className="box-border w-full rounded-md border border-border-strong bg-surface py-2 pl-9 pr-3 text-sm text-foreground shadow-sm transition-colors placeholder:text-muted hover:border-border-hover focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            onChange={event => setQuery(event.target.value)}
            placeholder={`Search ${remoteName}`}
            type="search"
            value={query}
          />
        </div>
        <button
          aria-label={
            isSearching ? `Searching ${remoteName}` : `Search ${remoteName}`
          }
          className="box-border inline-flex size-9 shrink-0 items-center justify-center rounded-md border border-primary bg-primary text-on-primary shadow-sm transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isSearching}
          type="submit"
        >
          {isSearching ? (
            <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
          ) : (
            <Search aria-hidden="true" className="size-4" />
          )}
        </button>
      </form>
      {error && <ErrorPanel error={error} title="Could not search records" />}
      <InvenioRDMRecordList
        records={records}
        includeDrafts={false}
        renderPreview={props => <InvenioRDMRecordPreview {...props} />}
        renderDetails={props => <InvenioRDMRecordRenderer {...props} />}
      />
    </div>
  );
};
