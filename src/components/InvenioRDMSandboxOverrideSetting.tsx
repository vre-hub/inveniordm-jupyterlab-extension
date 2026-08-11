import React from 'react';

import { setRemoteServerOverride, useRemoteServerOverride } from '../store';
import { InvenioRDMRemoteServerDropdown } from './InvenioRDMRemoteServerDropdown';

export const InvenioRDMSandboxOverrideSetting: React.FC = () => {
  const remoteServerOverride = useRemoteServerOverride();

  return (
    <label className="block">
      <span className="block text-sm font-medium text-foreground-secondary">
        Override environment
      </span>
      <span className="mt-1 block text-xs leading-5 text-muted">
        Use the environment from your login, or force a specific endpoint.
      </span>
      <div className="mt-2">
        <InvenioRDMRemoteServerDropdown
          ariaLabel={`Remote server override`}
          defaultOptionLabel="None (use default server)"
          onChange={value => setRemoteServerOverride(value)}
          value={remoteServerOverride}
        />
      </div>
    </label>
  );
};
