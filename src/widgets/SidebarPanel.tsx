import React from 'react';
import { VDomRenderer } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services';

import { requestAPI } from '../request';

const PANEL_CLASS = 'jp-ZenodoExtensionPanel';

interface IPanelProps {
  serverSettings: ServerConnection.ISettings;
}

const Panel: React.FC<IPanelProps> = ({ serverSettings }) => {
  const [accessToken, setAccessToken] = React.useState('');
  const [message, setMessage] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  const checkAccessToken = async (): Promise<void> => {
    setIsLoading(true);
    setMessage('');

    try {
      const response = await requestAPI<{ access_token_present: boolean }>(
        'access-token',
        serverSettings
      );
      setMessage(
        response.access_token_present
          ? 'An access token is stored.'
          : 'No access token is stored.'
      );
    } catch (reason) {
      setMessage(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

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
      const response = await requestAPI<{ message: string }>(
        'access-token',
        serverSettings,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_token: token })
        }
      );
      setMessage(response.message);
      setAccessToken('');
    } catch (reason) {
      setMessage(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  const deleteAccessToken = async (): Promise<void> => {
    setIsLoading(true);
    setMessage('');

    try {
      const response = await requestAPI<{ message: string }>(
        'access-token',
        serverSettings,
        {
          method: 'DELETE'
        }
      );
      setMessage(response.message);
    } catch (reason) {
      setMessage(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={PANEL_CLASS}>
      <form onSubmit={submitAccessToken}>
        <input
          aria-label="Zenodo access token"
          autoComplete="off"
          onChange={event => setAccessToken(event.target.value)}
          placeholder="Access token"
          type="password"
          value={accessToken}
        />
        <button disabled={isLoading || !accessToken.trim()} type="submit">
          {isLoading ? 'Saving...' : 'Save'}
        </button>
      </form>
      <button disabled={isLoading} onClick={checkAccessToken} type="button">
        Check token
      </button>
      <button disabled={isLoading} onClick={deleteAccessToken} type="button">
        Delete token
      </button>
      {message ? <p>{message}</p> : null}
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
