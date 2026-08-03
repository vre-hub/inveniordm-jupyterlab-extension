import React from 'react';
import {
  ZenodoVersionedRecordBase,
  ZenodoVersionedRecordBaseProps
} from '../core';

type ZenodoVersionedRecordProps = Omit<
  ZenodoVersionedRecordBaseProps,
  'renderLoadingError' | 'renderLoading' | 'renderRecordDeleted'
>;

/**
 * Display a single Zenodo record for the user.
 * Pass an initialRecordValue to avoid an additional API call if the record data is already available.
 */
export function ZenodoVersionedRecord(
  props: ZenodoVersionedRecordProps
): JSX.Element {
  return (
    <ZenodoVersionedRecordBase
      {...props}
      renderLoadingError={error => <div>{error}</div>}
      renderLoading={<div>Loading...</div>}
      renderRecordDeleted={<div>Record deleted</div>}
    />
  );
}
