import React from 'react';

import type { InvenioRDMRecordData } from '../api_calls';

type published_but_being_edited = 'published_but_being_edited';

type RecordStatusToDisplay =
  InvenioRDMRecordData['status'] | published_but_being_edited;

const STATUS_STYLES: Record<
  RecordStatusToDisplay,
  { label: string; className: string }
> = {
  published: {
    label: 'Published',
    className: 'bg-success-subtle text-success'
  },
  draft: {
    label: 'Draft',
    className: 'bg-warning-surface text-warning-strong'
  },
  new_version_draft: {
    label: 'New version draft',
    className: 'bg-primary-subtle text-primary-hover'
  },
  published_but_being_edited: {
    label: 'Edit published version',
    className: 'bg-warning-surface text-warning-strong'
  }
};

/** Displays a visual label for a record's publication status. */
export const InvenioRDMRecordStatus: React.FC<{
  status: InvenioRDMRecordData['status'];
  is_draft: boolean;
}> = ({ status, is_draft }) => {
  // If the record is a draft but the status is "published", we want to display that info
  const displayStatus: RecordStatusToDisplay =
    is_draft && status === 'published' ? 'published_but_being_edited' : status;

  const { label, className } = Object.entries(STATUS_STYLES).find(
    ([key]) => key === displayStatus
  )?.[1] ?? { label: displayStatus, className: 'bg-muted text-muted-strong' };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${className}`}
    >
      {label}
    </span>
  );
};
