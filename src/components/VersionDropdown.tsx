import React from 'react';

import { listZenodoRecordVersions, ZenodoRecordVersion } from '../api_calls';
import { useServerSettings } from '../store';

export function VersionDropdown({
  recordId,
  onChange
}: {
  recordId: string;
  onChange: (recordId: string) => void;
}): JSX.Element {
  const serverSettings = useServerSettings();
  const [versions, setVersions] = React.useState<ZenodoRecordVersion[]>([]);

  React.useEffect(() => {
    void listZenodoRecordVersions(serverSettings, recordId).then(
      (versions: ZenodoRecordVersion[]) => {
        console.log('Versions for record', recordId, versions);
        setVersions(versions);
      }
    );
  }, [recordId, serverSettings]);

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
  const versionNumber =
    version.versions?.index ??
    (version.metadata?.relations?.version?.[0]?.index !== undefined
      ? version.metadata.relations.version[0].index + 1
      : undefined);
  const isDraft = version.status === 'draft';
  const id = version.id;
  const label =
    `Version ${versionNumber} (${id})` + (isDraft ? ' (Draft)' : '');
  return (
    <option key={version.id} value={String(version.id)}>
      {label}
    </option>
  );
}
