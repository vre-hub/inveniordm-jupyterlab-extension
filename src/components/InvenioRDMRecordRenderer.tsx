import React from 'react';

import { InvenioRDMFileInfo } from './InvenioRDMFileInfo';
import {
  InvenioRDMRecordData,
  InvenioRDMRecordIdentifier,
  InvenioRDMRecordVersion
} from '../api_calls';
import { VersionDropdown } from './VersionDropdown';
import { InvenioRDMRecordActions } from './InvenioRDMRecordActions';
import { InvenioRDMRecordFileUpload } from './InvenioRDMRecordFileUpload';
import { RecordActionProvider, RecordActionStatus } from './RecordActionStatus';

export type InvenioRDMRecordRendererProps = {
  record: InvenioRDMRecordData;
  versions: InvenioRDMRecordVersion[];
  selectRecord: (identifier: InvenioRDMRecordIdentifier) => void;
  recordIdentifier: InvenioRDMRecordIdentifier; // TODO we need to pass this so that pending versions are displayed correctly in the dropdown. Maybe refactor this to avoid passing the identifier separately.
  hasEditingRights?: boolean;
};

const HumanReadableDate: React.FC<{ value: string }> = ({ value }) => {
  const date = new Date(value);

  return (
    <time
      dateTime={value}
      title={new Intl.DateTimeFormat(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short'
      }).format(date)}
    >
      {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date)}
    </time>
  );
};

export const InvenioRDMRecordRenderer: React.FC<
  InvenioRDMRecordRendererProps
> = ({
  record,
  hasEditingRights = false,
  versions,
  recordIdentifier,
  selectRecord
}) => {
  const isDraft = record.is_draft;
  const editable = isDraft && hasEditingRights;
  const files = Object.values(record.files?.entries ?? {});

  return (
    <div className="relative mb-3 rounded-lg border border-border bg-surface px-2 py-3 shadow-sm">
      <section>
        <InvenioRDMRecordRendererHeader
          record={record}
          hasEditingRights={hasEditingRights}
          versions={versions}
          recordIdentifier={recordIdentifier}
          selectRecord={selectRecord}
        />
        <div className="mt-2">
          {files.map(file => (
            <InvenioRDMFileInfo
              file={file}
              key={file.key}
              recordId={record.id}
              isDraft={record.is_draft}
              editable={editable}
            />
          ))}
        </div>
        {editable && <InvenioRDMRecordFileUpload recordId={record.id} />}
      </section>
    </div>
  );
};

export const InvenioRDMRecordPreview: React.FC<
  InvenioRDMRecordRendererProps
> = props => (
  <div className="relative mb-3 cursor-pointer rounded-lg border border-border bg-surface px-2 py-3 shadow-sm transition-all duration-200 hover:border-primary hover:shadow-md active:shadow-sm">
    <InvenioRDMRecordRendererHeader {...props} />
  </div>
);

export const InvenioRDMRecordRendererHeader: React.FC<
  InvenioRDMRecordRendererProps
> = ({
  record,
  hasEditingRights = false,
  versions,
  recordIdentifier,
  selectRecord
}) => {
  const refresh = (): void => {
    selectRecord(recordIdentifier);
  };
  return (
    <RecordActionProvider>
      <div>
        <div className="m-0 mb-1 pr-8 text-lg font-semibold text-foreground">
          {record.metadata?.title || 'Untitled Draft'}
        </div>
        <div className="absolute right-2 top-2">
          <InvenioRDMRecordActions
            record={record}
            versions={versions}
            hasEditingRights={hasEditingRights}
            refresh={refresh}
          />
        </div>
        <div className="mb-2 flex items-center gap-2">
          <div className="min-w-0 flex-1">
            <VersionDropdown
              versions={versions}
              recordIdentifier={recordIdentifier}
              onChange={identifier => {
                selectRecord(identifier);
              }}
            />
          </div>
        </div>
        <div className="mb-1 text-xs text-muted">
          <div>ID: {record.id}</div>
          <div>
            Created: <HumanReadableDate value={record.created} />
          </div>
          <div>
            Modified: <HumanReadableDate value={record.updated} />
          </div>
          {record.pids?.doi?.identifier ? (
            <div>DOI: {record.pids.doi.identifier}</div>
          ) : null}
          {`${record.files?.count ?? 0} file${record.files?.count === 1 ? '' : 's'}`}{' '}
          in this record.
        </div>
      </div>
      <RecordActionStatus />
    </RecordActionProvider>
  );
};
