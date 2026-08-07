import React from 'react';
import { ChevronDown } from 'lucide-react';

import { useRemoteServers } from '../core';
import { RemoteServerId } from '../remoteServers';

type RemoteServerSelectionValue = 'default' | RemoteServerId;

type ZenodoRemoteServerDropdownProps = {
  value: RemoteServerId | undefined;
  onChange: (value: RemoteServerId | undefined) => void;
  ariaLabel?: string;
  defaultOptionLabel?: string;
  className?: string;
};

function toSelectValue(
  remoteServerOverride: RemoteServerId | undefined
): RemoteServerSelectionValue {
  if (remoteServerOverride === undefined) {
    return 'default';
  }

  return remoteServerOverride;
}

function fromSelectValue(
  value: RemoteServerSelectionValue
): RemoteServerId | undefined {
  if (value === 'default') {
    return undefined;
  }

  return value;
}

export const ZenodoRemoteServerDropdown: React.FC<
  ZenodoRemoteServerDropdownProps
> = ({
  value,
  onChange,
  ariaLabel = 'Zenodo remote server',
  defaultOptionLabel = 'Default',
  className
}) => {
  const remoteServers = useRemoteServers();

  return (
    <div className={className}>
      <div className="relative block">
        <select
          aria-label={ariaLabel}
          className="box-border w-full appearance-none rounded-md border border-border-strong bg-surface px-3 py-2 pr-9 text-sm text-foreground shadow-sm transition-colors hover:border-border-hover focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          onChange={event =>
            onChange(
              fromSelectValue(event.target.value as RemoteServerSelectionValue)
            )
          }
          value={toSelectValue(value)}
        >
          <option value="default">{defaultOptionLabel}</option>
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
      </div>
    </div>
  );
};
