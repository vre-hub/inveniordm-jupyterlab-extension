import React from 'react';
import { Download } from 'lucide-react';

import { SelectDownloadDirectory } from './DownloadDirectoryPicker';

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
    </div>
  );
}
