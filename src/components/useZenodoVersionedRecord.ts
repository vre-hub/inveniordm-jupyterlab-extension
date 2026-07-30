import React from 'react';
import {
  listZenodoRecordVersions,
  ZenodoRecordData,
  ZenodoRecordVersion,
  ZenodoRecordVersionsChangedEventData
} from '../api_calls';
import { useEventListener } from '../sse';
import { useServerSettings } from '../store';

function sortVersions(versions: ZenodoRecordVersion[]): ZenodoRecordVersion[] {
  return [...versions].sort((a, b) => a.versions.index - b.versions.index);
}

export function useZenodoVersionedRecord({
  initialRecordId,
  initialRecordValue,
  include_drafts_in_version_dropdown,
  fetchRecord
}: {
  initialRecordId: string;
  initialRecordValue?: ZenodoRecordData;
  include_drafts_in_version_dropdown: boolean;
  fetchRecord: (id: string) => Promise<ZenodoRecordData>;
}) {
  /**
   * State for the currently displayed record ID.
   * This can change when the user selects a different version.
   * Use setRecordId to change the currently displayed record ID.
   * recordDeleted is set to true when the currently displayed record has been deleted.s
   */
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

  return {
    recordId,
    setRecordId,
    record,
    isLoading,
    loadRecord,
    recordDeleted,
    versions
  };
}
