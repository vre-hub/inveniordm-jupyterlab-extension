import React from 'react';
import { ChevronDown } from 'lucide-react';

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
    <div className="relative inline-block max-w-full">
      <select
        aria-label="Record version"
        className="box-border max-w-full appearance-none rounded-md border border-border-strong bg-surface py-2 pl-3 pr-9 text-sm text-foreground-secondary shadow-sm transition-colors hover:border-border-hover focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
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
      <ChevronDown
        aria-hidden="true"
        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted"
        size={16}
      />
    </div>
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
