import React from 'react';
import {
  listZenodoRecordVersions,
  ZenodoRecordData,
  ZenodoRecordIdentifier,
  ZenodoRecordVersion,
  ZenodoRecordVersionsChangedEventData,
  zenodoRecordIdentifierFromRecord
} from '../api_calls';
import { useEventListener } from '../sse';
import { useServerSettings } from '../store';

function sortVersions(versions: ZenodoRecordVersion[]): ZenodoRecordVersion[] {
  return [...versions].sort((a, b) => a.versions.index - b.versions.index);
}

export function useZenodoVersionedRecord({
  initialRecordIdentifier,
  initialRecordValue,
  include_drafts_in_version_dropdown,
  fetchRecord
}: {
  initialRecordIdentifier: ZenodoRecordIdentifier;
  initialRecordValue?: ZenodoRecordData;
  include_drafts_in_version_dropdown: boolean;
  fetchRecord: (
    identifier: ZenodoRecordIdentifier
  ) => Promise<ZenodoRecordData>;
}) {
  /**
   * State for the currently displayed record identifier.
   * This can change when the user selects a different version.
   * Use setRecordIdentifier to change the currently displayed record.
   * recordDeleted is set to true when the currently displayed record has been deleted.
   */
  const [recordIdentifier, setRecordIdentifier] =
    React.useState<ZenodoRecordIdentifier>(initialRecordIdentifier);

  const [record, setRecord] = React.useState<
    ZenodoRecordData | { error: string } | null
  >(initialRecordValue ?? null);
  const [isLoading, setIsLoading] = React.useState(false);
  const fetchRecordRef = React.useRef(fetchRecord);
  React.useEffect(() => {
    fetchRecordRef.current = fetchRecord;
  }, [fetchRecord]);

  const loadRecord = React.useCallback(
    async (
      identifier: ZenodoRecordIdentifier = recordIdentifier
    ): Promise<void> => {
      try {
        const record = await fetchRecordRef.current(identifier);
        setRecord(record);
        console.log('Loaded record', record);
      } catch (reason) {
        setRecord({ error: String(reason) });
      }
    },
    [recordIdentifier]
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
  useEventListener(
    `record.changed.${encodeURIComponent(recordIdentifier.record_id)}`,
    () => {
      void loadRecord();
    }
  );

  const [recordDeleted, setRecordDeleted] = React.useState(false);

  const [versions, setVersions] = React.useState<ZenodoRecordVersion[]>([]);
  const includeDrafts = include_drafts_in_version_dropdown;
  const serverSettings = useServerSettings();

  React.useEffect(() => {
    let isMounted = true;
    void listZenodoRecordVersions(
      serverSettings,
      initialRecordIdentifier.record_id,
      includeDrafts
    ).then(versions => {
      if (isMounted) {
        setVersions(sortVersions(versions));
      }
    });
    return () => {
      isMounted = false;
    };
  }, [includeDrafts, initialRecordIdentifier.record_id, serverSettings]);

  const parentId = versions.find(version => version.parent?.id)?.parent?.id;
  useEventListener('record.versions.changed', event => {
    const eventData = event.data as
      ZenodoRecordVersionsChangedEventData | undefined;

    if (
      !eventData ||
      (eventData.record_id !== recordIdentifier.record_id &&
        (!parentId || eventData.parent_id !== parentId))
    ) {
      return;
    }

    const correctedVersions = sortVersions(eventData.versions);
    setVersions(correctedVersions);

    if (
      eventData.type === 'version_created' &&
      eventData.record_id === recordIdentifier.record_id &&
      eventData.record
    ) {
      setRecordIdentifier(zenodoRecordIdentifierFromRecord(eventData.record));
      setRecord(eventData.record);
      return;
    }

    if (
      eventData.type === 'draft_discarded' &&
      recordIdentifier.record_status === 'draft' &&
      eventData.discarded_draft_id === recordIdentifier.record_id
    ) {
      const latestVersion = [...correctedVersions].reverse()[0];
      if (latestVersion) {
        setRecordIdentifier(zenodoRecordIdentifierFromRecord(latestVersion));
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
    recordIdentifier,
    setRecordIdentifier,
    record,
    isLoading,
    loadRecord,
    recordDeleted,
    versions
  };
}
