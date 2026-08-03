import React from 'react';
import {
  ZenodoRecordRenderer,
  ZenodoRecordRendererProps
} from './ZenodoRecordRenderer';
import { useHasEditingRights } from '../core/useHasEditingRights';

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
