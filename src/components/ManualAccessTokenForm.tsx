import React from 'react';

import {
  deleteAccessToken,
  putAccessToken
} from '../api_calls';
import { useServerSettings } from '../store';

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export const ManualAccessTokenForm: React.FC = () => {
  const serverSettings = useServerSettings();
  const [accessToken, setAccessToken] = React.useState('');
  const [message, setMessage] = React.useState('');

  const saveAccessToken = async (
    event: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    event.preventDefault();
    setMessage('');

    try {
      const status = await putAccessToken(serverSettings, accessToken);
      setAccessToken('');
      setMessage(`${status.message}`);
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
    }
  };

  const removeAccessToken = async (): Promise<void> => {
    setMessage('');

    try {
      await deleteAccessToken(serverSettings);
      setAccessToken('');
      setMessage('Token removed');
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
    }
  };

  return (
    <form onSubmit={saveAccessToken}>
      <label>
        Access token
        <input
          onChange={event => setAccessToken(event.currentTarget.value)}
          type="password"
          value={accessToken}
        />
      </label>
      <button disabled={!accessToken} type="submit">
        Save token
      </button>
      <button
        onClick={() => {
          void removeAccessToken();
        }}
        type="button"
      >
        Remove token
      </button>
      {message ? <div>{message}</div> : null}
    </form>
  );
};
