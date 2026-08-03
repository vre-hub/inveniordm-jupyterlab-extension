import React from 'react';

import { ZenodoFileInfo } from './ZenodoFileInfo';
import { OpenRecordButton } from './OpenRecordButton';
import { ZenodoRecordData, ZenodoRecordVersion } from '../api_calls';
import { CreateNewVersionButton } from './CreateNewVersionButton';
import { DiscardDraftButton } from './DiscardDraftButton';
import { ZenodoRecordFileUpload } from './ZenodoRecordFileUpload';

/**
 * Display the details of a Zenodo record.
 */
const ZenodoRecordDetails: React.FC<{
  record: ZenodoRecordData;
  editable: boolean;
}> = ({ record, editable }) => {
  const files = Object.values(record.files?.entries ?? {});
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
              isDraft={record.is_draft}
              editable={editable}
            />
          ))}
        </div>
      </section>
    </section>
  );
};

export const ZenodoRecordRenderer: React.FC<{
  record: ZenodoRecordData;
  versions: ZenodoRecordVersion[];
  hasEditingRights?: boolean;
}> = ({ record, versions, hasEditingRights = false }) => {
  const isDraft = record.is_draft;
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
    </section>
  );
};
