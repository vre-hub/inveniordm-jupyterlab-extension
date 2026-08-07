import React from 'react';
import { ChevronDown } from 'lucide-react';

import { RemoteServerId } from '../remoteServers';
import { setRemoteServerOverride, useRemoteServerOverride } from '../store';
import { useRemoteServers } from '../core';

type RemoteServerOverrideValue = 'default' | RemoteServerId;

function toSelectValue(
  remoteServerOverride: RemoteServerId | undefined
): RemoteServerOverrideValue {
  if (remoteServerOverride === undefined) {
    return 'default';
  }

  return remoteServerOverride;
}

function fromSelectValue(
  value: RemoteServerOverrideValue
): RemoteServerId | undefined {
  if (value === 'default') {
    return undefined;
  }

  return value;
}

export const ZenodoSandboxOverrideSetting: React.FC = () => {
  const remoteServerOverride = useRemoteServerOverride();
  const remoteServers = useRemoteServers();

  return (
    <label className="block">
      <span className="block text-sm font-medium text-foreground-secondary">
        Zenodo environment
      </span>
      <span className="mt-1 block text-xs leading-5 text-muted">
        Use the environment from your login, or force a specific endpoint.
      </span>
      <span className="relative mt-2 block">
        <select
          aria-label="Zenodo sandbox override"
          className="box-border w-full appearance-none rounded-md border border-border-strong bg-surface px-3 py-2 pr-9 text-sm text-foreground shadow-sm transition-colors hover:border-border-hover focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          onChange={event =>
            setRemoteServerOverride(
              fromSelectValue(event.target.value as RemoteServerOverrideValue)
            )
          }
          value={toSelectValue(remoteServerOverride)}
        >
          <option value="default">Use login environment</option>
          {remoteServers.map(remoteServer => (
            <option key={remoteServer.id} value={remoteServer.id}>
              {remoteServer.label}
            </option>
          ))}
        </select>
        <ChevronDown
          aria-hidden="true"
          className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted"
        />
      </span>
    </label>
  );
};
