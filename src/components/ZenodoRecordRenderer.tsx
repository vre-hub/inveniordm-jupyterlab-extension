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
  const files = Object.values(record.files?.entries ?? {});
  const refresh = (): void => {
    selectRecord(recordIdentifier);
  };

  return (
    <RecordActionProvider>
      <div className="relative mb-3 rounded-lg border border-border bg-surface px-2 py-3 shadow-sm">
        <section>
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
            <ZenodoRecordActions
              record={record}
              versions={versions}
              hasEditingRights={hasEditingRights}
              refresh={refresh}
            />
          </div>
          {record.metadata?.title && (
            <div className="m-0 mb-1 pr-8 text-sm font-semibold text-foreground">
              {record.metadata?.title}
            </div>
          )}
          <div className="mb-1 text-xs text-muted">
            <div>ID: {record.id}</div>
            {record.pids?.doi?.identifier ? (
              <div>DOI: {record.pids.doi.identifier}</div>
            ) : null}
          </div>
          <div className="mt-2">
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
          {editable && <ZenodoRecordFileUpload recordId={record.id} />}
          <RecordActionStatus />
        </section>
      </div>
    </RecordActionProvider>
  );
};
