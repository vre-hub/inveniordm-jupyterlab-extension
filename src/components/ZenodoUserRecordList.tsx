import React from 'react';

import {
  ZenodoRecordData,
  ZenodoRecordIdentifier,
  zenodoRecordIdentifierFromRecord
} from '../api_calls';
import { ZenodoVersionedRecord } from './ZenodoVersionedRecord';
import { ZenodoUserRecordDetails } from './ZenodoUserRecordDetails';
import { useZenodoUserRecords } from '../core/useZenodoUserRecords';

export const ZenodoUserRecordList: React.FC = () => {
  const { records, isLoading } = useZenodoUserRecords();

  return (
    <div>
      <h2>My Records</h2>
      {isLoading && <p>Loading...</p>}
      {Array.isArray(records)
        ? records.map(record => (
            <React.Fragment key={record.id}>
              <ZenodoUserRecord
                initialRecordIdentifier={zenodoRecordIdentifierFromRecord(
                  record
                )}
                initialRecordValue={record}
              />
            </React.Fragment>
          ))
        : records?.error}
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
