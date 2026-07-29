import React from 'react';
import {
  ZenodoRecordData,
  ZenodoRecordVersion,
  useZenodoRecordPermission
} from '../api_calls';
import { CreateNewVersionButton } from './CreateNewVersionButton';
import { DiscardDraftButton } from './DiscardDraftButton';
import { ZenodoRecordDetails } from './ZenodoRecordDetails';
import { ZenodoRecordFileUpload } from './ZenodoRecordFileUpload';

/**
 * Display the details of a Zenodo record for the user.
 * Request the api to check the user's permission for the record and display the appropriate actions.
 */
export const ZenodoUserRecordDetails: React.FC<{
  record: ZenodoRecordData;
  versions: ZenodoRecordVersion[];
}> = ({ record, versions }) => {
  const isDraft = record.is_draft;
  const userPermission = useZenodoRecordPermission(
    record.id,
    isDraft ? 'draft' : 'published'
  );
  const hasEditingRights =
    userPermission === 'edit' || userPermission === 'manage';
  const editable = isDraft && hasEditingRights;

  return (
    <section>
      <ZenodoRecordDetails record={record} editable={editable} />
      <CreateNewVersionButton
        id={record.id}
        versions={versions}
        allowedToCreateNewVersion={hasEditingRights}
      />
      {isDraft && (
        <DiscardDraftButton
          id={record.id}
          allowedToDiscardDraft={hasEditingRights}
        />
      )}
      {editable && (
        <>
          <ZenodoRecordFileUpload recordId={record.id} />
        </>
      )}
      <p>Access Rights: {userPermission}</p>
    </section>
  );
};
