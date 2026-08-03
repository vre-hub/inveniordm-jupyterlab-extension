import React from 'react';
import { useDiscardDraft } from '../core/useDiscardDraft';

export function DiscardDraftButton({
  id,
  allowedToDiscardDraft
}: {
  id: string;
  allowedToDiscardDraft: boolean;
}): JSX.Element {
  const { discardDraft, isLoading, error, hint } = useDiscardDraft(
    id,
    allowedToDiscardDraft
  );

  return (
    <>
      <button
        disabled={!allowedToDiscardDraft || isLoading}
        onClick={() => void discardDraft()}
        type="button"
        title={hint}
      >
        {isLoading ? 'Discarding...' : 'Discard Draft'}
      </button>
      {error ? <span>{error}</span> : null}
    </>
  );
}
