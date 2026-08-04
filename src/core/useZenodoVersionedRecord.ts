import React from 'react';
import { ServerConnection } from '@jupyterlab/services';
import {
  getZenodoRecordVariant,
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
  return [...versions].sort(
    (a, b) =>
      a.versions.index - b.versions.index ||
      Number(a.is_draft) - Number(b.is_draft)
  );
}

/** Choose the record representation to display after a draft is discarded. */
export function selectVersionAfterDraftDiscard(
  versions: ZenodoRecordVersion[],
  discardedDraftId: string
): ZenodoRecordVersion | undefined {
  return (
    versions.find(
      version => version.id === discardedDraftId && !version.is_draft
    ) ?? [...versions].reverse()[0]
  );
}

export function useZenodoVersionedRecord({
  initialRecordIdentifier,
  initialRecordValue,
  include_drafts_in_version_dropdown
}: {
  initialRecordIdentifier: ZenodoRecordIdentifier;
  initialRecordValue?: ZenodoRecordData;
  include_drafts_in_version_dropdown: boolean;
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
  const [recordDeleted, setRecordDeleted] = React.useState(false);
  const [versions, setVersions] = React.useState<ZenodoRecordVersion[]>([]);
  const serverSettings = useServerSettings();

  const loadRecord = React.useCallback(
    async (
      identifier: ZenodoRecordIdentifier = recordIdentifier
    ): Promise<void> => {
      try {
        const record = await getZenodoRecordVariant(serverSettings, identifier);
        setRecord(record);
        console.log('Loaded record', record);
      } catch (reason) {
        // Recover from a 404 error when the record is a draft that has been discarded from external sources (e.g. Zenodo web interface)
        if (
          reason instanceof ServerConnection.ResponseError &&
          reason.response.status === 404 &&
          identifier.record_status === 'draft'
        ) {
          const remainingVersions = versions.filter(
            version =>
              !(version.id === identifier.record_id && version.is_draft)
          );
          setVersions(remainingVersions);
          const nextVersion = selectVersionAfterDraftDiscard(
            remainingVersions,
            identifier.record_id
          );
          if (nextVersion) {
            const nextIdentifier =
              zenodoRecordIdentifierFromRecord(nextVersion);
            setRecordIdentifier(nextIdentifier);
            setRecord(
              await getZenodoRecordVariant(serverSettings, nextIdentifier)
            );
          } else {
            setRecordDeleted(true);
          }
          return;
        }
        setRecord({ error: String(reason) });
      }
    },
    [recordIdentifier, serverSettings, versions]
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

  const includeDrafts = include_drafts_in_version_dropdown;

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
      (eventData.record_id === recordIdentifier.record_id ||
        eventData.parent_id === parentId) &&
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
      const nextVersion = selectVersionAfterDraftDiscard(
        correctedVersions,
        eventData.discarded_draft_id
      );
      if (nextVersion) {
        const nextIdentifier = zenodoRecordIdentifierFromRecord(nextVersion);
        setRecordIdentifier(nextIdentifier);
        console.log(
          'Record discarded, switching record representation:',
          nextVersion
        );
        void loadRecord(nextIdentifier);
      } else {
        setVersions([]);
        setRecordDeleted(true);
      }
      return;
    }
  });

  const selectRecord = React.useCallback(
    (identifier: ZenodoRecordIdentifier) => {
      setRecordIdentifier(identifier);
      void loadRecord(identifier);
    },
    [loadRecord]
  );

  return {
    recordIdentifier,
    record,
    isLoading,
    selectRecord,
    recordDeleted,
    versions
  };
}
