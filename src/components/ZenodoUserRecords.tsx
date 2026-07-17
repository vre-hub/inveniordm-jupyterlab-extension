import React from 'react';

import { getZenodoUserRecord, listZenodoUserRecords } from '../api_calls';
import { useServerSettings } from '../store';
import { ZenodoResourceData } from '../api_calls';
import { ZenodoRecord } from './ZenodoRecord';

export const ZenodoUserRecords: React.FC = () => {
  const serverSettings = useServerSettings();
  const [records, setRecords] = React.useState<
    ZenodoResourceData[] | { error: string } | null
  >(null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadRecords = React.useCallback(async (): Promise<void> => {
    setIsLoading(true);

    try {
      setRecords(
        (await listZenodoUserRecords(serverSettings)) as ZenodoResourceData[]
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
  initialRecordValue?: ZenodoResourceData;
}): JSX.Element {
  const serverSettings = useServerSettings();
  return (
    <div>
      <ZenodoRecord
        initialRecordId={initialRecordId}
        initialRecordValue={initialRecordValue}
        fetchRecord={async (id: string): Promise<ZenodoResourceData> => {
          return await getZenodoUserRecord(serverSettings, id);
        }}
      />
    </div>
  );
}
