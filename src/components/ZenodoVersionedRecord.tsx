import React from 'react';
import { ZenodoRecordData, ZenodoRecordIdentifier } from '../api_calls';
import { useZenodoVersionedRecord } from '../core';
import { ZenodoRecordRendererProps } from './ZenodoRecordRenderer';

/**
 * Display a single Zenodo record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
export function ZenodoVersionedRecord({
  initialRecordIdentifier,
  initialRecordValue,
  include_drafts_in_version_dropdown,
  renderRecord
}: {
  initialRecordIdentifier: ZenodoRecordIdentifier;
  initialRecordValue?: ZenodoRecordData;
  include_drafts_in_version_dropdown: boolean;
  renderRecord: (props: ZenodoRecordRendererProps) => JSX.Element;
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
    return (
      <div>
        <p>This record has been deleted.</p>
      </div>
    );
  }

  const renderProps: ZenodoRecordRendererProps = {
    record: record as ZenodoRecordData,
    recordIdentifier,
    versions,
    selectRecord
  };

  return (
    <>
      {record && !('error' in record)
        ? renderRecord(renderProps)
        : record?.error}
      {isLoading && <p>Loading...</p>}
    </>
  );
}
