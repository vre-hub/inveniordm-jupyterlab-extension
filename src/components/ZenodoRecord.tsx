import React from 'react';
import { ZenodoResourceData } from '../api_calls';
import { useEventListener } from '../sse';
import { useServerSettings } from '../store';
import { VersionDropdown } from './VersionDropdown';
import { ZenodoResource } from './ZenodoResource';

/**
 * Display a single Zenodo record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
export function ZenodoRecord({
  initialRecordId,
  initialRecordValue,
  fetchRecord
}: {
  initialRecordId: string;
  initialRecordValue?: ZenodoResourceData;
  fetchRecord: (id: string) => Promise<ZenodoResourceData>;
}): JSX.Element {
  const [recordId, setRecordId] = React.useState<string>(initialRecordId);

  const serverSettings = useServerSettings();
  const [record, setRecord] = React.useState<
    ZenodoResourceData | { error: string } | null
  >(initialRecordValue ?? null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadRecord = React.useCallback(
    async (id: string = recordId): Promise<void> => {
      try {
        const record = await fetchRecord(id);
        setRecord(record);
      } catch (reason) {
        setRecord({ error: String(reason) });
      } finally {
      }
    },
    [serverSettings, recordId]
  );

  // If no initial record value is provided, load the record data from the API.
  React.useEffect(() => {
    if (!record) {
      setIsLoading(true);
      void loadRecord();
      setIsLoading(false);
    }
  }, [loadRecord]);

  // Listen for record changes via SSE and reload the record data when it changes.
  useEventListener(`record.changed.${encodeURIComponent(recordId)}`, event => {
    // If there is a new version, we need to update the recordId to the new version
    const eventData = event.data as
      { type?: string; new_version_id?: string } | undefined;
    if (
      eventData &&
      eventData.type === 'version_created' &&
      eventData.new_version_id
    ) {
      console.log(
        `New version created for record ${recordId}: ${eventData.new_version_id}`
      );
      setRecordId(eventData.new_version_id);
      setTimeout(() => {
        void loadRecord(eventData.new_version_id);
      }, 200); // record is not immediately available
      return;
    }
    // Otherwise, just reload the current record
    else {
      void loadRecord();
    }
  });

  return (
    <div>
      {isLoading && <p>Loading...</p>}
      <VersionDropdown
        recordId={recordId}
        onChange={id => {
          setRecordId(id);
          void loadRecord(id);
        }}
      />
      {record && !('error' in record) ? (
        <ZenodoResource resource={record} />
      ) : (
        record?.error
      )}
    </div>
  );
}
