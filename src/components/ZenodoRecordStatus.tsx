import React from 'react';

import type { ZenodoRecordData } from '../api_calls';

const STATUS_STYLES: Record<
  ZenodoRecordData['status'],
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
  }
};

export const ZenodoRecordStatus: React.FC<{
  status: ZenodoRecordData['status'];
}> = ({ status }) => {
  const { label, className } = Object.entries(STATUS_STYLES).find(
    ([key]) => key === status
  )?.[1] ?? { label: status, className: 'bg-muted text-muted-strong' };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${className}`}
    >
      {label}
    </span>
  );
};
