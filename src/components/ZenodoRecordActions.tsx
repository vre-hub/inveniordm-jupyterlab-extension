import React from 'react';
import { ExternalLink, GitBranchPlus, RefreshCw, Trash2 } from 'lucide-react';

import { ZenodoRecordData, ZenodoRecordVersion } from '../api_calls';
import { useCreateNewVersion, useDiscardDraft } from '../core';
import { OverflowMenu, OverflowMenuItem } from './OverflowMenu';
import { useRecordAction } from './RecordActionStatus';

export const ZenodoRecordActions: React.FC<{
  record: ZenodoRecordData;
  versions: ZenodoRecordVersion[];
  hasEditingRights: boolean;
  refresh: () => void;
}> = ({ record, versions, hasEditingRights, refresh }) => {
  const { setRecordAction } = useRecordAction();
  const editable = record.is_draft && hasEditingRights;
  const {
    createVersion,
    isLoading: isCreatingVersion,
    error: createVersionError,
    disable: disableCreateVersion,
    hint: createVersionHint
  } = useCreateNewVersion(versions, hasEditingRights);
  const {
    discardDraft,
    isLoading: isDiscardingDraft,
    error: discardDraftError,
    hint: discardDraftHint
  } = useDiscardDraft(record.id, hasEditingRights);

  const openRecord = (): void => {
    const newTab = window.open(record.links.self_html, '_blank');
    if (newTab) {
      newTab.focus();
    } else {
      console.error('Failed to open new tab for URL:', record.links.self_html);
    }
  };

  const actions: OverflowMenuItem[] = [
    {
      label: editable ? 'Edit Record' : 'Open Record',
      icon: <ExternalLink size={16} />,
      onClick: openRecord
    },
    {
      label: 'Refresh',
      icon: <RefreshCw size={16} />,
      hint: 'Reload the record from Zenodo',
      onClick: refresh
    },
    {
      label: isCreatingVersion ? 'Creating...' : 'Create New Version',
      hint: createVersionHint,
      icon: <GitBranchPlus size={16} />,
      onClick: () => {
        setRecordAction({
          description: 'Creating a new version…',
          icon: <GitBranchPlus size={16} />
        });
        void createVersion().finally(() => setRecordAction(null));
      },
      disabled: disableCreateVersion || isCreatingVersion
    },
    ...(record.is_draft
      ? [
          {
            label: isDiscardingDraft ? 'Discarding...' : 'Discard Draft',
            hint: discardDraftHint,
            icon: <Trash2 size={16} />,
            onClick: () => {
              setRecordAction({
                description: 'Discarding draft…',
                icon: <Trash2 size={16} />
              });
              void discardDraft().finally(() => setRecordAction(null));
            },
            disabled: !hasEditingRights || isDiscardingDraft,
            destructive: true
          }
        ]
      : [])
  ];

  return (
    <>
      <div className="absolute right-3 top-3">
        <OverflowMenu items={actions} label="Record actions" />
      </div>
      {createVersionError ? <span>{createVersionError}</span> : null}
      {discardDraftError ? <span>{discardDraftError}</span> : null}
    </>
  );
};
