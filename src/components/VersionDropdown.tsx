import React from 'react';

import {
  ZenodoRecordIdentifier,
  ZenodoRecordVersion,
  zenodoRecordIdentifierFromRecord
} from '../api_calls';
import { Dropdown, DropdownOption } from './Dropdown';
import { ZenodoRecordStatus } from './ZenodoRecordStatus';

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
  const selectedKey = recordIdentifierKey(recordIdentifier);

  return (
    <Dropdown
      ariaLabel="Record version"
      emptyLabel="No versions"
      listboxLabel="Record versions"
      onChange={value => {
        const selectedIdentifier = findRecordIdentifier(versions, value);
        if (selectedIdentifier) {
          onChange(selectedIdentifier);
        }
      }}
      value={selectedKey}
    >
      {versions.map(version => {
        const identifier = zenodoRecordIdentifierFromRecord(version);
        const value = recordIdentifierKey(identifier);

        return (
          <DropdownOption key={value} value={value}>
            <VersionDropdownContent version={version} />
          </DropdownOption>
        );
      })}
    </Dropdown>
  );
}

function VersionDropdownContent({
  version
}: {
  version: ZenodoRecordVersion;
}): JSX.Element {
  const versionNumber = version.versions.index;
  return (
    <>
      <span className="font-semibold text-foreground">{`Version ${versionNumber}`}</span>
      <ZenodoRecordStatus status={version.status} />
    </>
  );
}
