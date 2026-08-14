import { AlertCircle } from 'lucide-react';
import React from 'react';

/** Displays an error message with an optional heading. */
export const ErrorPanel: React.FC<{ error: string; title?: string }> = ({
  error,
  title
}) => {
  return (
    <div
      className="flex items-start gap-2 rounded-lg border border-danger-border bg-danger-subtle px-2 py-3 text-danger shadow-sm"
      role="alert"
    >
      <AlertCircle aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
      <div className="min-w-0">
        <div className="text-sm font-semibold">{title || 'Error'}</div>
        <div className="mt-0.5 break-words text-sm">{error}</div>
      </div>
    </div>
  );
};
