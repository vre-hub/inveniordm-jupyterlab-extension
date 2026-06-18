import React from 'react';
import { ServerConnection } from '@jupyterlab/services';

import { deleteAccessToken, putAccessToken } from '../api_calls';
import { LoginStatusPill } from './LoginStatusPill';

interface IZenodoLoginFormProps {
  serverSettings: ServerConnection.ISettings;
}

export const ZenodoLoginForm: React.FC<IZenodoLoginFormProps> = ({
  serverSettings
}) => {
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
    <>
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
    </>
  );
};
