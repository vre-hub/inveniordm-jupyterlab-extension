import React from 'react';

import { ZenodoFileInfo } from './ZenodoFileInfo';
import { OpenRecordButton } from './OpenRecordButton';
import { RecordUpload } from './RecordUpload';
import { CreateNewVersionButton } from './CreateNewVersionButton';
import {
  useRecordPermissions,
  ZenodoFile,
  ZenodoResourceData
} from '../api_calls';

// TODO this normalizes legacy and new file formats, check if we still need this
const getFiles = (files: ZenodoResourceData['files']): ZenodoFile[] => {
  if (Array.isArray(files)) {
    return files;
  }
  return files?.entries ?? [];
};

export const ZenodoResource: React.FC<{
  resource: ZenodoResourceData;
}> = ({ resource }) => {
  const isDraft =
    resource.status === 'draft' || resource.status === 'new_version_draft';
  const userPermissions = useRecordPermissions(resource.id);
  const hasEditingRights =
    userPermissions == 'edit' || userPermissions == 'manage';
  const editable = isDraft && hasEditingRights;
  const canCreateNewVersion = !isDraft && hasEditingRights;

  return (
    <section>
      <h4>{resource.metadata?.title ?? resource.id}</h4>
      <div>ID: {resource.id}</div>
      {resource.pids?.doi?.identifier ? (
        <div>DOI: {resource.pids.doi.identifier}</div>
      ) : null}
      <div>Status: {resource.status}</div>
      {canCreateNewVersion && <CreateNewVersionButton id={resource.id} />}
      <div>
        {getFiles(resource.files).map(file => (
          <ZenodoFileInfo
            file={file}
            key={file.key}
            recordId={resource.id}
            editable={editable}
          />
        ))}
      </div>
      <OpenRecordButton
        resource={resource}
        text={editable ? 'Edit Record' : 'Open Record'}
      />
      {editable && (
        <>
          <RecordUpload
            recordId={resource.id}
            onDone={() => {
              // TODO refresh the resource data after upload or other edits
            }}
          />
        </>
      )}
      <p>Access Rights: {userPermissions}</p>
    </section>
  );
};
