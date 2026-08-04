import React from 'react';
import { ExternalLink } from 'lucide-react';

type ZenodoRecordLink = {
  links: {
    self_html: string;
  };
};

/**
 * A button that opens a Zenodo record in a new tab.
 */
export function OpenRecordButton({
  record,
  text
}: {
  record: ZenodoRecordLink;
  text: string;
}): JSX.Element {
  const url = record.links.self_html;
  return (
    <button
      className="box-border inline-flex max-w-full items-center justify-center gap-2 rounded-md border border-primary bg-primary px-3 py-2 text-sm font-medium text-on-primary shadow-sm transition-colors hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      onClick={() => openLinkInNewTab(url)}
      type="button"
    >
      <span className="truncate">{text}</span>
      <ExternalLink aria-hidden="true" className="shrink-0" size={16} />
    </button>
  );
}

function openLinkInNewTab(url: string): void {
  const newTab = window.open(url, '_blank');
  if (newTab) {
    newTab.focus();
  } else {
    console.error('Failed to open new tab for URL:', url);
  }
}
