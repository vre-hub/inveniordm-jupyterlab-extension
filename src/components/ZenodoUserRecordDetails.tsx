import React from 'react';
import {
  ZenodoRecordRenderer,
  ZenodoRecordPreview,
  ZenodoRecordRendererProps
} from './ZenodoRecordRenderer';
import { useHasEditingRights } from '../core';

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

export const ZenodoUserRecordPreview: React.FC<
  ZenodoUserRecordDetailsProps
> = props => {
  const hasEditingRights = useHasEditingRights(props.record);

  return <ZenodoRecordPreview {...props} hasEditingRights={hasEditingRights} />;
};
