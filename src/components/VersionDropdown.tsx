import React from 'react';

import {
  ZenodoRecordIdentifier,
  ZenodoRecordVersion,
  zenodoRecordIdentifierFromRecord
} from '../api_calls';

/** Return a stable UI key for a record representation. */
export function recordIdentifierKey(
  identifier: ZenodoRecordIdentifier
): string {
  return `${identifier.record_status}:${identifier.record_id}`;
}

/** Resolve a dropdown key to the corresponding record identifier. */
export function findRecordIdentifier(
  versions: ZenodoRecordVersion[],
  identifierKey: string
): ZenodoRecordIdentifier | undefined {
  const version = versions.find(
    candidate =>
      recordIdentifierKey(zenodoRecordIdentifierFromRecord(candidate)) ===
      identifierKey
  );
  return version ? zenodoRecordIdentifierFromRecord(version) : undefined;
}

export function VersionDropdown({
  recordIdentifier,
  versions,
  onChange
}: {
  recordIdentifier: ZenodoRecordIdentifier;
  versions: ZenodoRecordVersion[];
  onChange: (identifier: ZenodoRecordIdentifier) => void;
}): JSX.Element {
  return (
    <select
      aria-label="Record version"
      className="box-border rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm transition-colors hover:border-slate-400 focus:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600/20"
      onChange={event => {
        const selectedIdentifier = findRecordIdentifier(
          versions,
          event.target.value
        );
        if (selectedIdentifier) {
          onChange(selectedIdentifier);
        }
      }}
      value={recordIdentifierKey(recordIdentifier)}
    >
      {versions.map(version => (
        <VersionDropdownOption
          version={version}
          key={recordIdentifierKey(zenodoRecordIdentifierFromRecord(version))}
        />
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
  const identifier = zenodoRecordIdentifierFromRecord(version);
  const label =
    `Version ${versionNumber} (${id})` + (isDraft ? ' (Draft)' : '');
  return <option value={recordIdentifierKey(identifier)}>{label}</option>;
}
