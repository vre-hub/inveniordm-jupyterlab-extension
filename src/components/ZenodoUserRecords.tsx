import React from 'react';

import { getZenodoUserRecord, listZenodoUserRecords } from '../api_calls';
import { useServerSettings } from '../store';
import { ZenodoResource } from './ZenodoResource';
import { ZenodoResourceData } from '../api_calls';
import { useEventListener } from '../sse';

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
              <ZenodoUserRecord initialRecordId={record.id} initialRecordValue={record} />
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
function ZenodoUserRecord({ initialRecordId, initialRecordValue }: { initialRecordId: string; initialRecordValue?: ZenodoResourceData }): JSX.Element {
  const [recordId, setRecordId] = React.useState<string>(initialRecordId);
  
  const serverSettings = useServerSettings();
  const [record, setRecord] = React.useState<
    ZenodoResourceData | { error: string } | null
  >(initialRecordValue ?? null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadRecord = React.useCallback(async (id: string = recordId): Promise<void> => {
    try {
      const record = await getZenodoUserRecord(serverSettings, id);
      setRecord(record);
    } catch (reason) {
      setRecord({ error: String(reason) });
    } finally {
    }
  }, [serverSettings, recordId]);

  // If no initial record value is provided, load the record data from the API.
  React.useEffect(() => {
    if (!record) {
      setIsLoading(true);
      void loadRecord();
      setIsLoading(false);
    }
  }, [loadRecord]);

  // Listen for record changes via SSE and reload the record data when it changes.
  useEventListener(`record.changed.${encodeURIComponent(recordId)}`, (event) => {
    // If there is a new version, we need to update the recordId to the new version
    const eventData = event.data as { type?: string; new_version_id?: string } | undefined;
    if (eventData && eventData.type === 'version_created' && eventData.new_version_id) {
      console.log(`New version created for record ${recordId}: ${eventData.new_version_id}`);
      setRecordId(eventData.new_version_id);
      setTimeout(() => {
        void loadRecord(eventData.new_version_id);
      }, 200); // record is not immediately available
      return;
    }
    // Otherwise, just reload the current record
    else{
      void loadRecord();
    }
  });

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