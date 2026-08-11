import React from 'react';

import {
  ZenodoUserRecordDetails,
  ZenodoUserRecordPreview
} from './ZenodoUserRecordDetails';
import { useZenodoUserRecords } from '../core';
import { LoadingPanel } from './LoadingPanel';
import { ZenodoRecordList } from './ZenodoRecordList';
import { ErrorPanel } from './ErrorPanel';

export const ZenodoUserRecordList: React.FC = () => {
  const { records, isLoading } = useZenodoUserRecords();

  if (isLoading) {
    return <LoadingPanel text="Loading records…" />;
  }

  if (records && 'error' in records) {
    return <ErrorPanel error={records.error} title="Could not load records" />;
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
