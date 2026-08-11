import React from 'react';
import { ChevronDown, Download, FlaskConical } from 'lucide-react';

import { SelectDownloadDirectory } from './DownloadDirectoryPicker';
import { InvenioRDMRemoteServerOverrideSetting } from './InvenioRDMRemoteServerOverrideSetting';

export function Settings(): JSX.Element {
  return (
    <div className="space-y-4">
      <section className="overflow-hidden rounded-lg border border-border bg-surface shadow-sm">
        <div className="flex items-start gap-2 border-b border-border bg-surface-muted px-2 py-3">
          <Download
            aria-hidden="true"
            className="mt-0.5 size-4 shrink-0 text-primary"
          />
          <div>
            <h2 className="m-0 text-sm font-semibold text-foreground">
              Download directory
            </h2>
            <p className="mb-0 mt-1 text-xs leading-5 text-muted">
              Choose where downloaded files are saved.
            </p>
          </div>
        </div>
        <div className="px-2 py-4">
          <SelectDownloadDirectory />
        </div>
      </section>
      <details className="group overflow-hidden rounded-lg border border-border bg-surface shadow-sm">
        <summary className="flex cursor-pointer list-none items-start gap-2 bg-surface-muted px-2 py-3 transition-colors hover:bg-surface-subtle focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary [&::-webkit-details-marker]:hidden">
          <FlaskConical
            aria-hidden="true"
            className="mt-0.5 size-4 shrink-0 text-warning"
          />
          <div className="min-w-0 flex-1">
            <h2 className="m-0 text-sm font-semibold text-foreground">
              Developer settings
            </h2>
          </div>
          <ChevronDown
            aria-hidden="true"
            className="mt-0.5 size-4 shrink-0 text-muted transition-transform group-open:rotate-180"
          />
        </summary>
        <div className="space-y-4 border-t border-border px-2 py-4">
          <InvenioRDMRemoteServerOverrideSetting />
        </div>
      </details>
    </div>
  );
}
