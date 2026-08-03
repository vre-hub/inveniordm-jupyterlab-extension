import React from 'react';
import { ZenodoRecordData, useZenodoRecordPermission } from '../api_calls';
import {
  ZenodoRecordRenderer,
  ZenodoRecordRendererProps
} from './ZenodoRecordRenderer';

type ZenodoUserRecordDetailsProps = Omit<
  ZenodoRecordRendererProps,
  'hasEditingRights'
>;

/**
 * Display the details of a Zenodo record for the user.
 * Request the api to check the user's permission for the record and display the appropriate actions.
 */
export const ZenodoUserRecordDetails: React.FC<
  ZenodoUserRecordDetailsProps
> = props => {
  const hasEditingRights = useHasEditingRights(props.record);

  return (
    <ZenodoRecordRenderer {...props} hasEditingRights={hasEditingRights} />
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
