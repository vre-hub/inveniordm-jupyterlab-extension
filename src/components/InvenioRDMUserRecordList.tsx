import React from 'react';

import {
  InvenioRDMUserRecordDetails,
  InvenioRDMUserRecordPreview
} from './InvenioRDMUserRecordDetails';
import { useInvenioRDMUserRecords } from '../core';
import { LoadingPanel } from './LoadingPanel';
import { InvenioRDMRecordList } from './InvenioRDMRecordList';
import { ErrorPanel } from './ErrorPanel';

/** Displays the signed-in user's records with pagination. */
export const InvenioRDMUserRecordList: React.FC = () => {
  const userRecords = useInvenioRDMUserRecords();
  const { isLoading, error } = userRecords;

  if (isLoading && userRecords.records.length === 0) {
    return <LoadingPanel text="Loading records…" />;
  }

  if (error) {
    return <ErrorPanel error={error} title="Could not load records" />;
  }

  return (
    <InvenioRDMRecordList
      pagination={userRecords}
      includeDrafts={true}
      renderPreview={props => <InvenioRDMUserRecordPreview {...props} />}
      renderDetails={props => <InvenioRDMUserRecordDetails {...props} />}
    />
  );
};
