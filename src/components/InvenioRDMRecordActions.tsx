import React from 'react';
import {
  AlertCircle,
  ExternalLink,
  GitBranchPlus,
  RefreshCw,
  Trash2
} from 'lucide-react';

import { InvenioRDMRecordData, InvenioRDMRecordVersion } from '../api_calls';
import {
  useCreateNewVersion,
  useCurrentRemoteServer,
  useDiscardDraft
} from '../core';
import { OverflowMenu, OverflowMenuItem } from './OverflowMenu';
import { useRecordAction } from './RecordActionStatus';

export const InvenioRDMRecordActions: React.FC<{
  record: InvenioRDMRecordData;
  versions: InvenioRDMRecordVersion[];
  hasEditingRights: boolean;
  refresh: () => void;
}> = ({ record, versions, hasEditingRights, refresh }) => {
  const { setRecordAction } = useRecordAction();
  const { remoteServer } = useCurrentRemoteServer();
  const remoteName = remoteServer?.display_name ?? 'remote repository';
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

  React.useEffect(() => {
    const error = createVersionError ?? discardDraftError;
    if (error) {
      setRecordAction({
        description: error,
        icon: <AlertCircle size={16} />,
        isLoading: false
      });
    }
  }, [createVersionError, discardDraftError, setRecordAction]);

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
      label: editable ? 'Edit Record Metadata' : `Open Record on ${remoteName}`,
      icon: <ExternalLink size={16} />,
      onClick: openRecord
    },
    {
      label: 'Refresh',
      icon: <RefreshCw size={16} />,
      hint: `Reload the record from ${remoteName}`,
      onClick: refresh
    },
    ...(hasEditingRights
      ? [
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
          }
        ]
      : []),
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

  return <OverflowMenu items={actions} label="Record actions" />;
};
