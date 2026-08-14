import React from 'react';
import { deleteInvenioRDMRecordDraft } from '../api_calls';
import { useServerSettings } from '../store';

/** Provides the availability and state of the discard-draft action. */
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
      await deleteInvenioRDMRecordDraft(serverSettings, id);
    } catch (reason) {
      setError(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  return { discardDraft, isLoading, error, hint };
}
