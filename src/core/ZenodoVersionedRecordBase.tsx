import React from 'react';
import { ZenodoRecordIdentifier, ZenodoRecordData } from '../api_calls';
import { useZenodoVersionedRecord } from '.';
import { ZenodoRecordRendererProps } from '../components/ZenodoRecordRenderer';

export type ZenodoVersionedRecordBaseProps = {
  initialRecordIdentifier: ZenodoRecordIdentifier;
  initialRecordValue?: ZenodoRecordData;
  include_drafts_in_version_dropdown: boolean;
  renderRecord: (props: ZenodoRecordRendererProps) => JSX.Element;
  renderLoadingError: (error: string) => JSX.Element;
  renderLoading: JSX.Element;
  renderRecordDeleted: JSX.Element;
};

/**
 * Display a single Zenodo record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
export function ZenodoVersionedRecordBase({
  initialRecordIdentifier,
  initialRecordValue,
  include_drafts_in_version_dropdown,
  renderRecord,
  renderLoadingError,
  renderLoading,
  renderRecordDeleted
}: {
  initialRecordIdentifier: ZenodoRecordIdentifier;
  initialRecordValue?: ZenodoRecordData;
  include_drafts_in_version_dropdown: boolean;
  renderRecord: (props: ZenodoRecordRendererProps) => JSX.Element;
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
  } = useZenodoVersionedRecord({
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

  const renderProps: ZenodoRecordRendererProps = {
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
