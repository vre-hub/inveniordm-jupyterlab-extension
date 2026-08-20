import React from 'react';

import {
  InvenioRDMRecordIdentifier,
  InvenioRDMRecordVersion,
  inveniordmRecordIdentifierFromRecord
} from '../api_calls';
import { Dropdown, DropdownOption } from './Dropdown';
import { InvenioRDMRecordStatus } from './InvenioRDMRecordStatus';

/** Return a stable UI key for a record representation. */
export function recordIdentifierKey(
  identifier: InvenioRDMRecordIdentifier
): string {
  return `${identifier.record_status}:${identifier.record_id}`;
}

/** Resolve a dropdown key to the corresponding record identifier. */
export function findRecordIdentifier(
  versions: InvenioRDMRecordVersion[],
  identifierKey: string
): InvenioRDMRecordIdentifier | undefined {
  const version = versions.find(
    candidate =>
      recordIdentifierKey(inveniordmRecordIdentifierFromRecord(candidate)) ===
      identifierKey
  );
  return version ? inveniordmRecordIdentifierFromRecord(version) : undefined;
}

/** Lets the user select a published or draft version of a record. */
export function VersionDropdown({
  isLoading,
  recordIdentifier,
  versions,
  onChange
}: {
  isLoading: boolean;
  recordIdentifier: InvenioRDMRecordIdentifier;
  versions: InvenioRDMRecordVersion[];
  onChange: (identifier: InvenioRDMRecordIdentifier) => void;
}): JSX.Element {
  const selectedKey = recordIdentifierKey(recordIdentifier);

  return (
    <Dropdown
      ariaLabel="Record version"
      emptyLabel="No versions"
      isLoading={isLoading}
      listboxLabel="Record versions"
      loadingLabel="Loading versions…"
      onChange={value => {
        const selectedIdentifier = findRecordIdentifier(versions, value);
        if (selectedIdentifier) {
          onChange(selectedIdentifier);
        }
      }}
      value={selectedKey}
    >
      {versions.map(version => {
        const identifier = inveniordmRecordIdentifierFromRecord(version);
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

/** Displays the label and status for a record version option. */
function VersionDropdownContent({
  version
}: {
  version: InvenioRDMRecordVersion;
}): JSX.Element {
  const versionNumber = version.versions.index;
  return (
    <>
      <span className="font-semibold text-foreground">{`Version ${versionNumber}`}</span>
      <InvenioRDMRecordStatus
        status={version.status}
        is_draft={version.is_draft}
      />
    </>
  );
}
