import React from 'react';
import { ZenodoRecordData, useZenodoRecordPermission } from '../api_calls';
import { CreateNewVersionButton } from './CreateNewVersionButton';
import { ZenodoRecordDetails } from './ZenodoRecordDetails';
import { ZenodoRecordFileUpload } from './ZenodoRecordFileUpload';

/**
 * Display the details of a Zenodo record for the user.
 * Request the api to check the user's permission for the record and display the appropriate actions.
 */
export const ZenodoUserRecordDetails: React.FC<{
  record: ZenodoRecordData;
}> = ({ record }) => {
  const isDraft = record.is_draft;
  const userPermission = useZenodoRecordPermission(record.id);
  const hasEditingRights =
    userPermission === 'edit' || userPermission === 'manage';
  const editable = isDraft && hasEditingRights;
  const canCreateNewVersion = !isDraft && hasEditingRights;

  return (
    <section>
      <ZenodoRecordDetails record={record} editable={editable} />
      {canCreateNewVersion && <CreateNewVersionButton id={record.id} />}
      {editable && (
        <>
          <ZenodoRecordFileUpload
            recordId={record.id}
            onDone={() => {
              // TODO refresh the resource data after upload or other edits
            }}
          />
        </>
      )}
      <p>Access Rights: {userPermission}</p>
    </section>
  );
};
