import React from 'react';
import { ServerConnection } from '@jupyterlab/services';

import { listZenodoDepositions } from '../api_calls';
import { ZenodoStore } from '../store';

interface IZenodoDepositionsProps {
  serverSettings: ServerConnection.ISettings;
}

export const ZenodoDepositions: React.FC<IZenodoDepositionsProps> = ({
  serverSettings
}) => {
  const [depositions, setDepositions] = React.useState<unknown>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const sandboxOverride = ZenodoStore.useState(state => state.sandboxOverride);

  const loadDepositions = async (): Promise<void> => {
    setIsLoading(true);

    try {
      setDepositions(
        await listZenodoDepositions(serverSettings, {
          sandbox: sandboxOverride
        })
      );
    } catch (reason) {
      setDepositions({ error: String(reason) });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <button disabled={isLoading} onClick={loadDepositions} type="button">
        {isLoading ? 'Loading...' : 'Load depositions'}
      </button>
      {depositions ? (
        <pre
          style={{
            maxHeight: '320px',
            maxWidth: '100%',
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}
        >
          {JSON.stringify(depositions, null, 2)}
        </pre>
      ) : null}
    </div>
  );
};
