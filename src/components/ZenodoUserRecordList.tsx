import React from 'react';

import { listZenodoUserRecords } from '../api_calls';
import { useServerSettings } from '../store';
import {
  ZenodoRecordData,
  ZenodoRecordIdentifier,
  zenodoRecordIdentifierFromRecord
} from '../api_calls';
import { ZenodoVersionedRecord } from './ZenodoVersionedRecord';
import { ZenodoUserRecordDetails } from './ZenodoUserRecordDetails';

export const ZenodoUserRecordList: React.FC = () => {
  const serverSettings = useServerSettings();
  const [records, setRecords] = React.useState<
    ZenodoRecordData[] | { error: string } | null
  >(null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadRecords = React.useCallback(async (): Promise<void> => {
    setIsLoading(true);

    try {
      setRecords(
        (await listZenodoUserRecords(serverSettings)) as ZenodoRecordData[]
      );
    } catch (reason) {
      setRecords({ error: String(reason) });
    } finally {
      setIsLoading(false);
    }
  }, [serverSettings]);

  React.useEffect(() => {
    void loadRecords();
  }, [loadRecords]);

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
