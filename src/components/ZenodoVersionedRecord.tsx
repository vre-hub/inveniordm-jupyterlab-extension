import React from 'react';
import { ZenodoRecordData } from '../api_calls';
import { useEventListener } from '../sse';
import { VersionDropdown } from './VersionDropdown';

/**
 * Display a single Zenodo record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
export function ZenodoVersionedRecord({
  initialRecordId,
  initialRecordValue,
  include_drafts_in_version_dropdown,
  fetchRecord,
  renderRecord
}: {
  initialRecordId: string;
  initialRecordValue?: ZenodoRecordData;
  include_drafts_in_version_dropdown: boolean;
  fetchRecord: (id: string) => Promise<ZenodoRecordData>;
  renderRecord: (record: ZenodoRecordData) => JSX.Element;
}): JSX.Element {
  const [recordId, setRecordId] = React.useState<string>(initialRecordId);

  const [record, setRecord] = React.useState<
    ZenodoRecordData | { error: string } | null
  >(initialRecordValue ?? null);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadRecord = React.useCallback(
    async (id: string = recordId): Promise<void> => {
      try {
        const record = await fetchRecord(id);
        setRecord(record);
      } catch (reason) {
        setRecord({ error: String(reason) });
      }
    },
    [recordId]
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
      | {
          type?: string;
          record?: ZenodoRecordData;
        }
      | undefined;
    if (eventData && eventData.type === 'version_created' && eventData.record) {
      console.log(
        `New version created for record ${recordId}: ${eventData.record.id}`
      );
      setRecordId(eventData.record.id);
      setRecord(eventData.record);
      return;
    }
    // Otherwise, just reload the current record
    else {
      void loadRecord();
    }
  });

  return (
    <div
      style={{
        border: '1px solid #ccc',
        padding: '1rem',
        borderRadius: '0.5rem'
      }}
    >
      {isLoading && <p>Loading...</p>}
      <VersionDropdown
        recordId={recordId}
        includeDrafts={include_drafts_in_version_dropdown}
        onChange={id => {
          setRecordId(id);
          void loadRecord(id);
        }}
      />
      {record && !('error' in record) ? renderRecord(record) : record?.error}
    </div>
  );
}
