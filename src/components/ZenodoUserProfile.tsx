import React from 'react';
import { AlertCircle, Mail, UserRound } from 'lucide-react';

import { useZenodoUserProfile } from '../core';

export const ZenodoUserProfile: React.FC = () => {
  const { profile, error } = useZenodoUserProfile();

  if (profile === null) {
    return error ? (
      <div
        className="flex items-start gap-2 rounded-md border border-danger-border bg-danger-subtle p-3 text-sm text-danger"
        role="alert"
      >
        <AlertCircle aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
        <span className="break-words">{error}</span>
      </div>
    ) : null;
  }

  return (
    <div className="mb-4 flex min-w-0 items-center gap-3 rounded-lg bg-primary-subtle p-3">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary text-on-primary shadow-sm">
        <UserRound aria-hidden="true" className="size-5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="m-0 text-xs font-medium uppercase tracking-wide text-primary-hover">
          Signed in to Zenodo
        </p>
        <p className="m-0 mt-1 flex min-w-0 items-center gap-1.5 text-sm font-semibold text-foreground">
          <Mail aria-hidden="true" className="size-3.5 shrink-0 text-muted" />
          <span className="truncate" title={profile.email}>
            {profile.email}
          </span>
        </p>
      </div>
    </div>
  );
};
