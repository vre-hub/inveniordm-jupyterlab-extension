import React from 'react';

import { setSandboxOverride, useSandboxOverride } from '../store';

type SandboxOverrideValue = 'default' | 'production' | 'sandbox';

function toSelectValue(
  sandboxOverride: boolean | undefined
): SandboxOverrideValue {
  if (sandboxOverride === undefined) {
    return 'default';
  }

  return sandboxOverride ? 'sandbox' : 'production';
}

function fromSelectValue(value: SandboxOverrideValue): boolean | undefined {
  if (value === 'default') {
    return undefined;
  }

  return value === 'sandbox';
}

export const ZenodoSandboxOverrideSetting: React.FC = () => {
  const sandboxOverride = useSandboxOverride();

  return (
    <label>
      Sandbox override
      <select
        aria-label="Zenodo sandbox override"
        onChange={event =>
          setSandboxOverride(
            fromSelectValue(event.target.value as SandboxOverrideValue)
          )
        }
        value={toSelectValue(sandboxOverride)}
      >
        <option value="default">Use login</option>
        <option value="production">Production</option>
        <option value="sandbox">Sandbox</option>
      </select>
    </label>
  );
};
