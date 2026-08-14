import React from 'react';
import { RotateCcw } from 'lucide-react';

import { setRemoteServerOverride, useRemoteServerOverride } from '../store';
import { useGetRemoteServersDefault } from '../core';
import { InvenioRDMRemoteServerDropdown } from './InvenioRDMRemoteServerDropdown';

/** Displays the setting for overriding the default InvenioRDM server. */
export const InvenioRDMRemoteServerOverrideSetting: React.FC = () => {
  const remoteServerOverride = useRemoteServerOverride();
  const defaultRemoteServer = useGetRemoteServersDefault();
  const selectedRemoteServer = remoteServerOverride ?? defaultRemoteServer?.id;

  return (
    <div className="block">
      <div className="mt-2 flex items-center gap-2">
        <InvenioRDMRemoteServerDropdown
          ariaLabel="Repository server"
          className="min-w-0 flex-1"
          onChange={value => setRemoteServerOverride(value)}
          useDefaultOption={false}
          value={selectedRemoteServer}
        />
        <button
          aria-label="Reset repository server"
          className="box-border inline-flex size-9 shrink-0 items-center justify-center rounded-md border border-border-strong bg-surface text-foreground-secondary shadow-sm transition-colors hover:border-border-hover hover:bg-surface-muted hover:text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-default disabled:opacity-50"
          disabled={remoteServerOverride === undefined}
          onClick={() => setRemoteServerOverride(undefined)}
          title="Reset to default repository server"
          type="button"
        >
          <RotateCcw aria-hidden="true" className="size-4" />
        </button>
      </div>
    </div>
  );
};
