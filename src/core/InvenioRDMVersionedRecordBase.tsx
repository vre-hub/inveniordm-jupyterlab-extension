import React from 'react';
import { InvenioRDMRecordIdentifier, InvenioRDMRecordData } from '../api_calls';
import { useInvenioRDMVersionedRecord } from '.';
import { InvenioRDMRecordRendererProps } from '../components/InvenioRDMRecordRenderer';

/** Properties for loading and rendering a selectable record version. */
export type InvenioRDMVersionedRecordBaseProps = {
  initialRecordIdentifier: InvenioRDMRecordIdentifier;
  initialRecordValue?: InvenioRDMRecordData;
  include_drafts_in_version_dropdown: boolean;
  renderRecord: (props: InvenioRDMRecordRendererProps) => JSX.Element;
  renderLoadingError: (error: string) => JSX.Element;
  renderLoading: JSX.Element;
  renderRecordDeleted: JSX.Element;
};

/**
 * Display a single InvenioRDM record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
export function InvenioRDMVersionedRecordBase({
  initialRecordIdentifier,
  initialRecordValue,
  include_drafts_in_version_dropdown,
  renderRecord,
  renderLoadingError,
  renderLoading,
  renderRecordDeleted
}: {
  initialRecordIdentifier: InvenioRDMRecordIdentifier;
  initialRecordValue?: InvenioRDMRecordData;
  include_drafts_in_version_dropdown: boolean;
  renderRecord: (props: InvenioRDMRecordRendererProps) => JSX.Element;
  renderLoadingError: (error: string) => JSX.Element;
  renderLoading: JSX.Element;
  renderRecordDeleted: JSX.Element;
}): JSX.Element {
  const {
    recordIdentifier,
    selectRecord,
    record,
    isLoading,
    recordDeleted,
    versions
  } = useInvenioRDMVersionedRecord({
    initialRecordIdentifier,
    initialRecordValue,
    include_drafts_in_version_dropdown
  });

  if (recordDeleted) {
    return renderRecordDeleted;
  }

  if (!record) {
    return renderLoading;
  }

  if ('error' in record) {
    return renderLoadingError(record.error);
  }

  const renderProps: InvenioRDMRecordRendererProps = {
    record,
    recordIdentifier,
    versions,
    selectRecord
  };

  return (
    <>
      {renderRecord(renderProps)}
      {isLoading && renderLoading}
    </>
  );
}
