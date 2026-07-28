import React from 'react';

import { listZenodoRecordVersions, ZenodoRecordVersion } from '../api_calls';
import { useServerSettings } from '../store';

export function VersionDropdown({
  recordId,
  includeDrafts,
  onChange
}: {
  recordId: string;
  includeDrafts: boolean;
  onChange: (recordId: string) => void;
}): JSX.Element {
  const serverSettings = useServerSettings();
  const [versions, setVersions] = React.useState<ZenodoRecordVersion[]>([]);

  React.useEffect(() => {
    void listZenodoRecordVersions(serverSettings, recordId, includeDrafts).then(
      (versions: ZenodoRecordVersion[]) => {
        setVersions(versions);
      }
    );
  }, [includeDrafts, recordId, serverSettings]);

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
