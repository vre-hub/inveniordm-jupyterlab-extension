import React from 'react';

import {
  InvenioRDMUserRecordDetails,
  InvenioRDMUserRecordPreview
} from './InvenioRDMUserRecordDetails';
import { useInvenioRDMUserRecords } from '../core';
import { LoadingPanel } from './LoadingPanel';
import { InvenioRDMRecordList } from './InvenioRDMRecordList';
import { ErrorPanel } from './ErrorPanel';

export const InvenioRDMUserRecordList: React.FC = () => {
  const { records, isLoading } = useInvenioRDMUserRecords();

  if (isLoading) {
    return <LoadingPanel text="Loading records…" />;
  }

  if (records && 'error' in records) {
    return <ErrorPanel error={records.error} title="Could not load records" />;
  }

  return (
    <InvenioRDMRecordList
      records={records ?? []}
      includeDrafts={true}
      renderPreview={props => <InvenioRDMUserRecordPreview {...props} />}
      renderDetails={props => <InvenioRDMUserRecordDetails {...props} />}
    />
  );
};
