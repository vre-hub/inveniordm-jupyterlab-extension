import { LoaderCircle } from 'lucide-react';
import React from 'react';

export function LoadingPanel({ text }: { text: string }): JSX.Element {
  return (
    <div
      aria-label={text}
      className="flex items-center justify-center gap-2 py-5 text-sm font-medium text-muted"
      role="status"
    >
      <LoaderCircle
        aria-hidden="true"
        className="size-5 animate-spin text-primary"
      />
      <span>{text}</span>
    </div>
  );
}
