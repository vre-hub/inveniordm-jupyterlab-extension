import React from 'react';
import { VDomRenderer } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services';

import {
  deleteAccessToken,
  putAccessToken,
  searchZenodoRecords
} from '../api_calls';
import { LoginStatusPill } from '../components/LoginStatusPill';

const PANEL_CLASS = 'jp-ZenodoExtensionPanel';

interface IPanelProps {
  serverSettings: ServerConnection.ISettings;
}

const ZenodoSearch: React.FC<IPanelProps> = ({ serverSettings }) => {
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<unknown>(null);
  const [isSearching, setIsSearching] = React.useState(false);

  const submitSearch = async (
    event: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    event.preventDefault();
    setIsSearching(true);

    try {
      setResults(await searchZenodoRecords(serverSettings, query));
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

const Panel: React.FC<IPanelProps> = ({ serverSettings }) => {
  const [accessToken, setAccessToken] = React.useState('');
  const [sandbox, setSandbox] = React.useState(false);
  const [message, setMessage] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  const submitAccessToken = async (
    event: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    event.preventDefault();

    const token = accessToken.trim();
    if (!token) {
      setMessage('Paste an access token first.');
      return;
    }

    setIsLoading(true);
    setMessage('');

    try {
      const response = await putAccessToken(serverSettings, token, sandbox);
      setMessage(response.message);
      setAccessToken('');
    } catch (reason) {
      setMessage(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  const deleteAccessTokenCall = async (): Promise<void> => {
    setIsLoading(true);
    setMessage('');

    try {
      const response = await deleteAccessToken(serverSettings);
      setMessage(response.message);
    } catch (reason) {
      setMessage(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={PANEL_CLASS}>
      <LoginStatusPill serverSettings={serverSettings} />
      <button
        disabled={isLoading}
        onClick={deleteAccessTokenCall}
        type="button"
      >
        Delete token
      </button>
      <hr />
      <form onSubmit={submitAccessToken}>
        <input
          aria-label="Zenodo access token"
          autoComplete="off"
          onChange={event => setAccessToken(event.target.value)}
          placeholder="Access token"
          type="password"
          value={accessToken}
        />
        <label>
          <input
            checked={sandbox}
            onChange={event => setSandbox(event.target.checked)}
            type="checkbox"
          />
          Sandbox
        </label>
        <button disabled={isLoading || !accessToken.trim()} type="submit">
          {isLoading ? 'Saving...' : 'Save'}
        </button>
      </form>
      {message ? <p>{message}</p> : null}
      <hr />
      <ZenodoSearch serverSettings={serverSettings} />
    </div>
  );
};

export class SidebarPanel extends VDomRenderer {
  constructor(private serverSettings: ServerConnection.ISettings) {
    super();
    super.addClass(PANEL_CLASS);
    super.title.label = 'Zenodo';
    super.title.caption = 'Zenodo Integration';
    super.title.closable = true;
  }

  render(): React.ReactElement {
    return <Panel serverSettings={this.serverSettings} />;
  }
}
