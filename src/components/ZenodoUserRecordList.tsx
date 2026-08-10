import React from 'react';
import { AlertCircle, ArrowLeft } from 'lucide-react';

import {
  ZenodoRecordData,
  ZenodoRecordIdentifier,
  zenodoRecordIdentifierFromRecord
} from '../api_calls';
import { ZenodoVersionedRecord } from './ZenodoVersionedRecord';
import {
  ZenodoUserRecordDetails,
  ZenodoUserRecordPreview
} from './ZenodoUserRecordDetails';
import { useZenodoUserRecords } from '../core';
import { LoadingPanel } from './LoadingPanel';
import {
  setSelectedUserRecordIdentifier,
  useSelectedUserRecordIdentifier
} from '../store';

// TODO refactor this to split rendering list from rendering selected record
export const ZenodoUserRecordList: React.FC = () => {
  const { records, isLoading } = useZenodoUserRecords();
  const selectedUserRecordIdentifier = useSelectedUserRecordIdentifier();

  if (isLoading) {
    return <LoadingPanel text="Loading records…" />;
  }

  if (records && 'error' in records) {
    return (
      <div
        className="flex items-start gap-2 rounded-lg border border-danger-border bg-danger-subtle px-2 py-3 text-danger shadow-sm"
        role="alert"
      >
        <AlertCircle aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
        <div className="min-w-0">
          <div className="text-sm font-semibold">Could not load records</div>
          <div className="mt-0.5 break-words text-sm">{records.error}</div>
        </div>
      </div>
    );
  }

  const selectedRecord = records?.find(record => {
    const identifier = zenodoRecordIdentifierFromRecord(record);
    return (
      identifier.record_id === selectedUserRecordIdentifier?.record_id &&
      identifier.record_status === selectedUserRecordIdentifier.record_status
    );
  });

  if (selectedUserRecordIdentifier && selectedRecord) {
    return (
      <div>
        <button
          className="mb-3 inline-flex items-center gap-1.5 rounded-md border border-border-strong bg-surface px-2.5 py-1.5 text-xs font-medium text-muted-strong shadow-sm transition-colors hover:border-primary hover:bg-primary-subtle hover:text-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          onClick={() => setSelectedUserRecordIdentifier(undefined)}
          type="button"
        >
          <ArrowLeft aria-hidden="true" className="size-3.5" />
          Back to records
        </button>
        <ZenodoUserRecord
          initialRecordIdentifier={selectedUserRecordIdentifier}
          initialRecordValue={selectedRecord}
        />
      </div>
    );
  }

  return (
    <div>
      {records?.map(record => {
        const recordIdentifier = zenodoRecordIdentifierFromRecord(record);
        return (
          <div
            key={`${recordIdentifier.record_status}:${recordIdentifier.record_id}`}
            onClick={event => {
              // Keep controls in the preview usable without opening the record.
              const element = event.target as HTMLElement;
              if (element.closest('button, a, input, select, textarea')) {
                return;
              }
              setSelectedUserRecordIdentifier(recordIdentifier);
            }}
          >
            <ZenodoVersionedRecord
              initialRecordIdentifier={recordIdentifier}
              initialRecordValue={record}
              include_drafts_in_version_dropdown={true}
              renderRecord={zenodoRecordRendererProps => (
                <ZenodoUserRecordPreview {...zenodoRecordRendererProps} />
              )}
            />
          </div>
        );
      })}
    </div>
  );
};

function ZenodoUserRecord({
  initialRecordIdentifier,
  initialRecordValue
}: {
  initialRecordIdentifier: ZenodoRecordIdentifier;
  initialRecordValue?: ZenodoRecordData;
}): JSX.Element {
  return (
    <div>
      <ZenodoVersionedRecord
        initialRecordIdentifier={initialRecordIdentifier}
        initialRecordValue={initialRecordValue}
        include_drafts_in_version_dropdown={true}
        renderRecord={zenodoRecordRendererProps => (
          <ZenodoUserRecordDetails {...zenodoRecordRendererProps} />
        )}
      />
    </div>
  );
}
