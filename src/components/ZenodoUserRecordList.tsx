import React from 'react';
import { AlertCircle } from 'lucide-react';

import {
  ZenodoRecordData,
  ZenodoRecordIdentifier,
  zenodoRecordIdentifierFromRecord
} from '../api_calls';
import { ZenodoVersionedRecord } from './ZenodoVersionedRecord';
import { ZenodoUserRecordDetails } from './ZenodoUserRecordDetails';
import { useZenodoUserRecords } from '../core';
import { LoadingPanel } from './LoadingPanel';

export const ZenodoUserRecordList: React.FC = () => {
  const { records, isLoading } = useZenodoUserRecords();

  if (isLoading) {
    return <LoadingPanel text="Loading records…" />;
  }

  if (records && 'error' in records) {
    return (
      <div
        className="flex items-start gap-3 rounded-lg border border-danger-border bg-danger-subtle p-4 text-danger shadow-sm"
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

  return (
    <div>
      {records?.map(record => (
        <React.Fragment key={record.id}>
          <ZenodoUserRecord
            initialRecordIdentifier={zenodoRecordIdentifierFromRecord(record)}
            initialRecordValue={record}
          />
        </React.Fragment>
      ))}
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
