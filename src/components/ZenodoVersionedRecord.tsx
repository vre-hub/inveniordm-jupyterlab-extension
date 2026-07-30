import React from 'react';
import {
  listZenodoRecordVersions,
  ZenodoRecordData,
  ZenodoRecordVersion,
  ZenodoRecordVersionsChangedEventData
} from '../api_calls';
import { useEventListener } from '../sse';
import { VersionDropdown } from './VersionDropdown';
import { useServerSettings } from '../store';

function sortVersions(versions: ZenodoRecordVersion[]): ZenodoRecordVersion[] {
  return [...versions].sort((a, b) => a.versions.index - b.versions.index);
}

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
  renderRecord: (
    record: ZenodoRecordData,
    versions: ZenodoRecordVersion[] // TODO we pass this versions array around a lot, think about better component structure
  ) => JSX.Element;
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
        console.log('Loaded record', record);
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

  // Listen for changes to the currently displayed record.
  useEventListener(`record.changed.${encodeURIComponent(recordId)}`, () => {
    void loadRecord();
  });

  const [recordDeleted, setRecordDeleted] = React.useState(false);

  const [versions, setVersions] = React.useState<ZenodoRecordVersion[]>([]);
  const includeDrafts = include_drafts_in_version_dropdown;
  const serverSettings = useServerSettings();

  React.useEffect(() => {
    let isMounted = true;
    void listZenodoRecordVersions(
      serverSettings,
      initialRecordId,
      includeDrafts
    ).then(versions => {
      if (isMounted) {
        setVersions(sortVersions(versions));
      }
    });
    return () => {
      isMounted = false;
    };
  }, [includeDrafts, initialRecordId, serverSettings]);

  const parentId = versions.find(version => version.parent?.id)?.parent?.id;
  useEventListener('record.versions.changed', event => {
    const eventData = event.data as
      ZenodoRecordVersionsChangedEventData | undefined;

    if (
      !eventData ||
      (eventData.record_id !== recordId &&
        (!parentId || eventData.parent_id !== parentId))
    ) {
      return;
    }

    const correctedVersions = sortVersions(eventData.versions);
    setVersions(correctedVersions);

    if (
      eventData.type === 'version_created' &&
      eventData.record_id === recordId &&
      eventData.record
    ) {
      setRecordId(eventData.record.id);
      setRecord(eventData.record);
      return;
    }

    if (
      eventData.type === 'draft_discarded' &&
      eventData.discarded_draft_id === recordId
    ) {
      const latestVersion = [...correctedVersions].reverse()[0];
      if (latestVersion) {
        setRecordId(latestVersion.id);
        console.log(
          'Record discarded, switching to latest version:',
          latestVersion
        );
        setRecord(latestVersion as unknown as ZenodoRecordData); // TODO check if this is actually correct
      } else {
        setVersions([]);
        setRecordDeleted(true);
      }
      return;
    }
  });

  if (recordDeleted) {
    return (
      <div>
        <p>This record has been deleted.</p>
      </div>
    );
  }

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
        versions={versions}
        recordId={recordId}
        onChange={id => {
          setRecordId(id);
          void loadRecord(id);
        }}
      />
      {record && !('error' in record)
        ? renderRecord(record, versions)
        : record?.error}
    </div>
  );
}
