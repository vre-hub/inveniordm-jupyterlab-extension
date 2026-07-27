import React from 'react';

import { getZenodoUserRecord, listZenodoUserRecords } from '../api_calls';
import { useServerSettings } from '../store';
import { ZenodoRecordData } from '../api_calls';
import { ZenodoVersionedRecord } from './ZenodoRecord';
import { ZenodoUserRecordDetails } from './ZenodoRecordDetails';

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
                initialRecordId={record.id}
                initialRecordValue={record}
              />
            </React.Fragment>
          ))
        : records?.error}
    </div>
  );
};

function ZenodoUserRecord({
  initialRecordId,
  initialRecordValue
}: {
  initialRecordId: string;
  initialRecordValue?: ZenodoRecordData;
}): JSX.Element {
  const serverSettings = useServerSettings();
  return (
    <div>
      <ZenodoVersionedRecord
        initialRecordId={initialRecordId}
        initialRecordValue={initialRecordValue}
        fetchRecord={async (id: string): Promise<ZenodoRecordData> => {
          return await getZenodoUserRecord(serverSettings, id);
        }}
        renderRecord={record => <ZenodoUserRecordDetails record={record} />}
      />
    </div>
  );
}
