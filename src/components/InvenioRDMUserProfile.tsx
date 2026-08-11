import React from 'react';
import { Mail, UserRound } from 'lucide-react';

import { useInvenioRDMUserProfile } from '../core';
import { ErrorPanel } from './ErrorPanel';

export const InvenioRDMUserProfile: React.FC = () => {
  const { profile, error } = useInvenioRDMUserProfile();

  if (profile === null) {
    return error ? <ErrorPanel error={error} /> : null;
  }

  return (
    <div className="mb-4 flex min-w-0 items-center gap-2 rounded-lg bg-primary-subtle px-2 py-3">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary text-on-primary shadow-sm">
        <UserRound aria-hidden="true" className="size-5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="m-0 text-xs font-medium uppercase tracking-wide text-primary-hover">
          Signed in as
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
