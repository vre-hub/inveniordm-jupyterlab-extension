import React from 'react';

import { ZenodoFileInfo } from './ZenodoFileInfo';
import { OpenRecordButton } from './OpenRecordButton';
import { ZenodoRecordData } from '../api_calls';

/**
 * Display the details of a Zenodo record.
 */
export const ZenodoRecordDetails: React.FC<{
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
              editable={editable}
            />
          ))}
        </div>
      </section>
    </section>
  );
};
