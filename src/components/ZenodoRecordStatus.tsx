import React from 'react';

import type { ZenodoRecordData } from '../api_calls';

const STATUS_STYLES: Record<
  ZenodoRecordData['status'],
  { label: string; className: string }
> = {
  published: {
    label: 'Published',
    className: 'bg-emerald-50 text-emerald-700'
  },
  draft: {
    label: 'Draft',
    className: 'bg-amber-100 text-amber-800'
  },
  new_version_draft: {
    label: 'New version draft',
    className: 'bg-blue-50 text-blue-700'
  }
};

export const ZenodoRecordStatus: React.FC<{
  status: ZenodoRecordData['status'];
}> = ({ status }) => {
  const { label, className } = STATUS_STYLES[status];

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${className}`}
    >
      {label}
    </span>
  );
};
