import React from 'react';
import { AlertCircle, LoaderCircle, Trash2, X } from 'lucide-react';

import {
  ZenodoVersionedRecordBase,
  ZenodoVersionedRecordBaseProps
} from '../core';

type ZenodoVersionedRecordProps = Omit<
  ZenodoVersionedRecordBaseProps,
  'renderLoadingError' | 'renderLoading' | 'renderRecordDeleted'
>;

/**
 * Display a single Zenodo record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
export function ZenodoVersionedRecord(
  props: ZenodoVersionedRecordProps
): JSX.Element {
  return (
    <ZenodoVersionedRecordBase
      {...props}
      renderLoadingError={error => <RecordLoadingError error={error} />}
      renderLoading={<RecordLoading />}
      renderRecordDeleted={<RecordDeleted />}
    />
  );
}

function RecordLoadingError({ error }: { error: string }): JSX.Element {
  return (
    <div
      className="flex items-start gap-2 rounded-lg border border-danger-border bg-danger-subtle px-2 py-3 text-danger shadow-sm"
      role="alert"
    >
      <AlertCircle aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
      <div className="min-w-0">
        <div className="text-sm font-semibold">Could not load record</div>
        <div className="mt-0.5 break-words text-sm">{error}</div>
      </div>
    </div>
  );
}

function RecordLoading(): JSX.Element {
  return (
    <div
      aria-label="Loading record"
      className="flex items-center justify-center gap-2 rounded-lg border border-border bg-surface-muted px-2 py-8 text-sm font-medium text-muted shadow-sm"
      role="status"
    >
      <LoaderCircle
        aria-hidden="true"
        className="size-5 animate-spin text-primary"
      />
      <span>Loading record…</span>
    </div>
  );
}

function RecordDeleted(): JSX.Element | null {
  const [isVisible, setIsVisible] = React.useState(true);

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className="flex items-center gap-2 rounded-lg border border-border bg-surface-muted px-2 py-3 shadow-sm"
      role="status"
    >
      <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-surface-subtle text-muted">
        <Trash2 aria-hidden="true" className="size-4" />
      </span>
      <div className="min-w-0">
        <div className="text-sm font-semibold text-foreground">
          Record deleted
        </div>
        <div className="text-xs text-muted">
          This Zenodo record is no longer available.
        </div>
      </div>
      <button
        aria-label="Dismiss deleted record notice"
        className="ml-auto inline-flex shrink-0 items-center gap-1.5 rounded-full border border-border-strong bg-surface px-2.5 py-1.5 text-xs font-medium text-muted-strong shadow-sm transition-all hover:border-primary hover:bg-primary-subtle hover:text-primary-hover hover:shadow-md active:translate-y-0 active:shadow-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        onClick={() => setIsVisible(false)}
        title="Dismiss"
        type="button"
      >
        <X aria-hidden="true" className="size-3.5" />
        <span>Dismiss</span>
      </button>
    </div>
  );
}
