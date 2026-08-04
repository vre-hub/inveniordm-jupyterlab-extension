import React from 'react';
import { ExternalLink, GitBranchPlus, Trash2 } from 'lucide-react';

import { ZenodoRecordData, ZenodoRecordVersion } from '../api_calls';
import { useCreateNewVersion, useDiscardDraft } from '../core';
import { OverflowMenu, OverflowMenuItem } from './OverflowMenu';

export const ZenodoRecordActions: React.FC<{
  record: ZenodoRecordData;
  versions: ZenodoRecordVersion[];
  hasEditingRights: boolean;
}> = ({ record, versions, hasEditingRights }) => {
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
      label: isCreatingVersion ? 'Creating...' : 'Create New Version',
      hint: createVersionHint,
      icon: <GitBranchPlus size={16} />,
      onClick: () => void createVersion(),
      disabled: disableCreateVersion || isCreatingVersion
    },
    ...(record.is_draft
      ? [
          {
            label: isDiscardingDraft ? 'Discarding...' : 'Discard Draft',
            hint: discardDraftHint,
            icon: <Trash2 size={16} />,
            onClick: () => void discardDraft(),
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
