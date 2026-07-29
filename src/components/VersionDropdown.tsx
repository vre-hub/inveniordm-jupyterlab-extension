import React from 'react';

import { ZenodoRecordVersion } from '../api_calls';

export function VersionDropdown({
  recordId,
  versions,
  onChange
}: {
  recordId: string;
  versions: ZenodoRecordVersion[];
  onChange: (recordId: string) => void;
}): JSX.Element {
  return (
    <select
      aria-label="Record version"
      onChange={event => onChange(event.target.value)}
      value={recordId}
    >
      {versions.map(version => (
        <VersionDropdownOption version={version} key={version.id} />
      ))}
    </select>
  );
}

function VersionDropdownOption({
  version
}: {
  version: ZenodoRecordVersion;
}): JSX.Element {
  const versionNumber = version.versions.index;
  const isDraft = version.is_draft;
  const id = version.id;
  const label =
    `Version ${versionNumber} (${id})` + (isDraft ? ' (Draft)' : '');
  return (
    <option key={version.id} value={String(version.id)}>
      {label}
    </option>
  );
}
