import React from 'react';

import { ZenodoFileInfo } from './ZenodoFileInfo';
import { OpenRecordButton } from './OpenRecordButton';
import { ZenodoRecordFileUpload } from './ZenodoRecordFileUpload';
import { CreateNewVersionButton } from './CreateNewVersionButton';
import { useZenodoRecordPermission, ZenodoRecordData } from '../api_calls';

export const ZenodoRecordDetails: React.FC<{
  record: ZenodoRecordData;
}> = ({ record }) => {
  const isDraft =
    record.status === 'draft' || record.status === 'new_version_draft';
  const userPermission = useZenodoRecordPermission(record.id);
  const hasEditingRights =
    userPermission === 'edit' || userPermission === 'manage';
  const editable = isDraft && hasEditingRights;
  const canCreateNewVersion = !isDraft && hasEditingRights;
  const files = record.files?.entries ?? [];

  return (
    <section>
      <h4>{record.metadata?.title ?? record.id}</h4>
      <div>ID: {record.id}</div>
      {record.pids?.doi?.identifier ? (
        <div>DOI: {record.pids.doi.identifier}</div>
      ) : null}
      <div>Status: {record.status}</div>
      {canCreateNewVersion && <CreateNewVersionButton id={record.id} />}
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
      <OpenRecordButton
        record={record}
        text={editable ? 'Edit Record' : 'Open Record'}
      />
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
