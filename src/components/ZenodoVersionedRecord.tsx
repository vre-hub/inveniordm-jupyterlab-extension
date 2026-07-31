import React from 'react';
import {
  ZenodoRecordData,
  ZenodoRecordIdentifier,
  ZenodoRecordVersion
} from '../api_calls';
import { VersionDropdown } from './VersionDropdown';
import { useZenodoVersionedRecord } from './useZenodoVersionedRecord';

/**
 * Display a single Zenodo record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
export function ZenodoVersionedRecord({
  initialRecordIdentifier,
  initialRecordValue,
  include_drafts_in_version_dropdown,
  fetchRecord,
  renderRecord
}: {
  initialRecordIdentifier: ZenodoRecordIdentifier;
  initialRecordValue?: ZenodoRecordData;
  include_drafts_in_version_dropdown: boolean;
  fetchRecord: (
    identifier: ZenodoRecordIdentifier
  ) => Promise<ZenodoRecordData>;
  renderRecord: (
    record: ZenodoRecordData,
    versions: ZenodoRecordVersion[] // TODO we pass this versions array around a lot, think about better component structure
  ) => JSX.Element;
}): JSX.Element {
  const {
    recordIdentifier,
    setRecordIdentifier,
    record,
    isLoading,
    loadRecord,
    recordDeleted,
    versions
  } = useZenodoVersionedRecord({
    initialRecordIdentifier,
    initialRecordValue,
    include_drafts_in_version_dropdown,
    fetchRecord
  });

  if (recordDeleted) {
    return (
      <div>
        <p>This record has been deleted.</p>
      </div>
    );
  }

  return (
    <div
      style={{
        border: '1px solid #ccc',
        padding: '1rem',
        borderRadius: '0.5rem'
      }}
    >
      {isLoading && <p>Loading...</p>}
      <VersionDropdown
        versions={versions}
        recordIdentifier={recordIdentifier}
        onChange={identifier => {
          setRecordIdentifier(identifier);
          void loadRecord(identifier);
        }}
      />
      {record && !('error' in record)
        ? renderRecord(record, versions)
        : record?.error}
    </div>
  );
}
