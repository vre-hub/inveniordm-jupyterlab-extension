import React from 'react';
import {
  InvenioRDMRecordRenderer,
  InvenioRDMRecordPreview,
  InvenioRDMRecordRendererProps
} from './InvenioRDMRecordRenderer';
import { useHasEditingRights } from '../core';

type InvenioRDMUserRecordDetailsProps = Omit<
  InvenioRDMRecordRendererProps,
  'hasEditingRights'
>;

/**
 * Display the details of a InvenioRDM record for the user.
 * Request the api to check the user's permission for the record and display the appropriate actions.
 */
export const InvenioRDMUserRecordDetails: React.FC<
  InvenioRDMUserRecordDetailsProps
> = props => {
  const hasEditingRights = useHasEditingRights(props.record);

  return (
    <InvenioRDMRecordRenderer {...props} hasEditingRights={hasEditingRights} />
  );
};

/** Displays a compact user-record preview without files but with permission-aware actions. */
export const InvenioRDMUserRecordPreview: React.FC<
  InvenioRDMUserRecordDetailsProps
> = props => {
  const hasEditingRights = useHasEditingRights(props.record);

  return (
    <InvenioRDMRecordPreview {...props} hasEditingRights={hasEditingRights} />
  );
};
