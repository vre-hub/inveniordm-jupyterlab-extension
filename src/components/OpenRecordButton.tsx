import React from 'react';

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
  return <button onClick={() => openLinkInNewTab(url)}>{text}</button>;
}

function openLinkInNewTab(url: string): void {
  const newTab = window.open(url, '_blank');
  if (newTab) {
    newTab.focus();
  } else {
    console.error('Failed to open new tab for URL:', url);
  }
}
