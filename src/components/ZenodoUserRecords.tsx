import React from 'react';

import { getZenodoUserRecord, listZenodoUserRecords } from '../api_calls';
import { useServerSettings } from '../store';
import { ZenodoResource } from './ZenodoResource';
import { ZenodoResourceData } from '../api_calls';

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
              <ZenodoUserRecord recordId={record.id} initialRecordValue={record} />
            </React.Fragment>
          ))
        : records?.error}
    </div>
  );
};

/**
 * Display a single Zenodo record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
function ZenodoUserRecord({ recordId, initialRecordValue }: { recordId: string; initialRecordValue?: ZenodoResourceData }): JSX.Element {
  const serverSettings = useServerSettings();
  const [record, setRecord] = React.useState<
    ZenodoResourceData | { error: string } | null
  >(initialRecordValue ?? null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadRecord = React.useCallback(async (): Promise<void> => {
    setIsLoading(true);

    try {
      const record = await getZenodoUserRecord(serverSettings, recordId);
      setRecord(record);
    } catch (reason) {
      setRecord({ error: String(reason) });
    } finally {
      setIsLoading(false);
    }
  }, [serverSettings, recordId]);

  React.useEffect(() => {
    if (!record) {
      void loadRecord();
    }
    else {
      console.log(`ZenodoUserRecord: Using initial record value for record ${recordId}`);
    }
  }, [loadRecord]);

  return (
    <div>
      {isLoading && <p>Loading...</p>}
      {record && !('error' in record) ? (
        <ZenodoResource resource={record} />
      ) : (
        record?.error
      )}
    </div>
  );
}