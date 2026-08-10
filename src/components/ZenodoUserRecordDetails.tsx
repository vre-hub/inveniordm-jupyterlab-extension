import React from 'react';
import {
  ZenodoRecordRenderer,
  ZenodoRecordRendererHeader,
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

  return (
    <div className="relative mb-3 cursor-pointer rounded-lg border border-border bg-surface px-2 py-3 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary hover:shadow-md active:translate-y-0 active:shadow-sm">
      <ZenodoRecordRendererHeader
        {...props}
        hasEditingRights={hasEditingRights}
      />
    </div>
  );
};
