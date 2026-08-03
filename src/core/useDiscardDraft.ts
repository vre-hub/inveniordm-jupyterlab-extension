import React from 'react';
import { deleteZenodoRecordDraft } from '../api_calls';
import { useServerSettings } from '../store';

export function useDiscardDraft(id: string, allowedToDiscardDraft: boolean) {
  const serverSettings = useServerSettings();
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const hint = allowedToDiscardDraft
    ? ''
    : 'You do not have permission to discard this draft.';

  const discardDraft = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await deleteZenodoRecordDraft(serverSettings, id);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  return { discardDraft, isLoading, error, hint };
}
