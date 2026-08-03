import React from 'react';
import {
  ZenodoRecordData,
  ZenodoRecordVersion,
  useZenodoRecordPermission
} from '../api_calls';
import { ZenodoRecordRenderer } from './ZenodoRecordDetails';

/**
 * Display the details of a Zenodo record for the user.
 * Request the api to check the user's permission for the record and display the appropriate actions.
 */
export const ZenodoUserRecordDetails: React.FC<{
  record: ZenodoRecordData;
  versions: ZenodoRecordVersion[];
}> = ({ record, versions }) => {
  const hasEditingRights = useHasEditingRights(record);

  return (
    <ZenodoRecordRenderer
      record={record}
      versions={versions}
      hasEditingRights={hasEditingRights}
    />
  );
};

function useHasEditingRights(record: ZenodoRecordData): boolean {
  const isDraft = record.is_draft;
  const userPermission = useZenodoRecordPermission(
    record.id,
    isDraft ? 'draft' : 'published'
  );
  return userPermission === 'edit' || userPermission === 'manage';
}
