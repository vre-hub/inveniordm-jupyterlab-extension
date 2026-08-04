import React from 'react';

import { ZenodoFileInfo } from './ZenodoFileInfo';
import {
  ZenodoRecordData,
  ZenodoRecordIdentifier,
  ZenodoRecordVersion
} from '../api_calls';
import { VersionDropdown } from './VersionDropdown';
import { ZenodoRecordActions } from './ZenodoRecordActions';
import { ZenodoRecordFileUpload } from './ZenodoRecordFileUpload';
import { RecordActionProvider, RecordActionStatus } from './RecordActionStatus';

export type ZenodoRecordRendererProps = {
  record: ZenodoRecordData;
  versions: ZenodoRecordVersion[];
  selectRecord: (identifier: ZenodoRecordIdentifier) => void;
  recordIdentifier: ZenodoRecordIdentifier; // TODO we need to pass this so that pending versions are displayed correctly in the dropdown. Maybe refactor this to avoid passing the identifier separately.
  hasEditingRights?: boolean;
};

export const ZenodoRecordRenderer: React.FC<ZenodoRecordRendererProps> = ({
  record,
  hasEditingRights = false,
  versions,
  recordIdentifier,
  selectRecord
}) => {
  const isDraft = record.is_draft;
  const editable = isDraft && hasEditingRights;

  return (
    <RecordActionProvider>
      <div
        className="relative"
        style={{
          border: '1px solid #ccc',
          padding: '1rem',
          borderRadius: '0.5rem'
        }}
      >
        <section>
          <VersionDropdown
            versions={versions}
            recordIdentifier={recordIdentifier}
            onChange={identifier => {
              selectRecord(identifier);
            }}
          />
          <ZenodoRecordDetails record={record} editable={editable} />
          <ZenodoRecordActions
            record={record}
            versions={versions}
            hasEditingRights={hasEditingRights}
          />
          <RecordActionStatus />
          {editable && <ZenodoRecordFileUpload recordId={record.id} />}
        </section>
      </div>
    </RecordActionProvider>
  );
};

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
