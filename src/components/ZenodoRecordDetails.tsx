import React from 'react';

import { ZenodoFileInfo } from './ZenodoFileInfo';
import { OpenRecordButton } from './OpenRecordButton';
import { ZenodoRecordFileUpload } from './ZenodoRecordFileUpload';
import { CreateNewVersionButton } from './CreateNewVersionButton';
import { useZenodoRecordPermission, ZenodoRecordData } from '../api_calls';

/**
 * Display the details of a Zenodo record for the user.
 * Request the api to check the user's permission for the record and display the appropriate actions.
 */
export const ZenodoUserRecordDetails: React.FC<{
  record: ZenodoRecordData;
}> = ({ record }) => {
  const isDraft =
    record.status === 'draft' || record.status === 'new_version_draft';
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

/**
 * Display the details of a Zenodo record.
 */
export const ZenodoRecordDetails: React.FC<{
  record: ZenodoRecordData;
  editable: boolean;
}> = ({ record, editable }) => {
  const files = record.files?.entries ?? [];
  return (
    <section>
      <section>
        <h4>{record.metadata?.title ?? record.id}</h4>
        <div>ID: {record.id}</div>
        {record.pids?.doi?.identifier ? (
          <div>DOI: {record.pids.doi.identifier}</div>
        ) : null}
        <div>Status: {record.status}</div>
        <OpenRecordButton
          record={record}
          text={editable ? 'Edit Record' : 'Open Record'}
        />
      </section>
      <section>
        <div>
          {files.map(file => (
            <ZenodoFileInfo
              file={file}
              key={file.key}
              recordId={record.id}
              editable={editable}
            />
          ))}
        </div>
      </section>
    </section>
  );
};
