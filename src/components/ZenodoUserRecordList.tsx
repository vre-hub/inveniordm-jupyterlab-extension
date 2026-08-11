import React from 'react';
import { AlertCircle } from 'lucide-react';

import {
  ZenodoUserRecordDetails,
  ZenodoUserRecordPreview
} from './ZenodoUserRecordDetails';
import { useZenodoUserRecords } from '../core';
import { LoadingPanel } from './LoadingPanel';
import { ZenodoRecordList } from './ZenodoRecordList';

export const ZenodoUserRecordList: React.FC = () => {
  const { records, isLoading } = useZenodoUserRecords();

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

  return (
    <ZenodoRecordList
      records={records ?? []}
      includeDrafts={true}
      renderPreview={props => <ZenodoUserRecordPreview {...props} />}
      renderDetails={props => <ZenodoUserRecordDetails {...props} />}
    />
  );
};
