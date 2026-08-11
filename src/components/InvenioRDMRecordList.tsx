import React from 'react';
import { ArrowLeft } from 'lucide-react';

import {
  InvenioRDMRecordData,
  InvenioRDMRecordIdentifier,
  inveniordmRecordIdentifierFromRecord
} from '../api_calls';
import { InvenioRDMRecordRendererProps } from './InvenioRDMRecordRenderer';
import { InvenioRDMVersionedRecord } from './InvenioRDMVersionedRecord';

type InvenioRDMRecordListProps = {
  records: InvenioRDMRecordData[];
  includeDrafts: boolean;
  renderPreview: (props: InvenioRDMRecordRendererProps) => JSX.Element;
  renderDetails: (props: InvenioRDMRecordRendererProps) => JSX.Element;
};

/**
 * Show record headers first, then replace the list with the selected record's
 * file details. Both public search results and a user's records use this flow.
 */
export const InvenioRDMRecordList: React.FC<InvenioRDMRecordListProps> = ({
  records,
  includeDrafts,
  renderPreview,
  renderDetails
}) => {
  const [selection, setSelection] = React.useState<
    | {
        identifier: InvenioRDMRecordIdentifier;
        record: InvenioRDMRecordData;
      }
    | undefined
  >();

  if (selection) {
    return (
      <div>
        <button
          className="mb-3 inline-flex items-center gap-1.5 rounded-md border border-border-strong bg-surface px-2.5 py-1.5 text-xs font-medium text-muted-strong shadow-sm transition-colors hover:border-primary hover:bg-primary-subtle hover:text-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          onClick={() => setSelection(undefined)}
          type="button"
        >
          <ArrowLeft aria-hidden="true" className="size-3.5" />
          Back to records
        </button>
        <InvenioRDMVersionedRecord
          initialRecordIdentifier={selection.identifier}
          initialRecordValue={selection.record}
          include_drafts_in_version_dropdown={includeDrafts}
          renderRecord={renderDetails}
        />
      </div>
    );
  }

  return (
    <div>
      {records.map(record => {
        const initialRecordIdentifier =
          inveniordmRecordIdentifierFromRecord(record);

        return (
          <InvenioRDMVersionedRecord
            key={`${initialRecordIdentifier.record_status}:${initialRecordIdentifier.record_id}`}
            initialRecordIdentifier={initialRecordIdentifier}
            initialRecordValue={record}
            include_drafts_in_version_dropdown={includeDrafts}
            renderRecord={props => (
              <div
                onClick={event => {
                  // Keep controls in the header usable without opening details.
                  const element = event.target as HTMLElement;
                  if (element.closest('button, a, input, select, textarea')) {
                    return;
                  }
                  setSelection({
                    identifier: props.recordIdentifier,
                    record: props.record
                  });
                }}
              >
                {renderPreview(props)}
              </div>
            )}
          />
        );
      })}
    </div>
  );
};
