import React from 'react';
import {
  Ban,
  CheckCircle2,
  CircleAlert,
  Clock3,
  LoaderCircle,
  X
} from 'lucide-react';

import { JobProgressProps, useJobProgressUpdates } from '../core';

export const JobProgress: React.FC<JobProgressProps> = props => {
  const { progress, progressLabel, canCancel, cancel, loadingProgress } =
    useJobProgressUpdates(props);

  if (loadingProgress || !progress) {
    return (
      <div
        className="box-border flex min-h-16 w-full items-center gap-2 rounded-lg border border-border bg-surface-muted px-2 py-3 text-xs text-muted shadow-sm"
        role="status"
      >
        <LoaderCircle aria-hidden="true" className="animate-spin" size={14} />
        Loading progress…
      </div>
    );
  }

  const hasTotal = progress.total_bytes !== null && progress.total_bytes > 0;
  const percentage = hasTotal
    ? Math.min(
        100,
        Math.max(
          0,
          Math.round(
            (progress.completed_bytes / (progress.total_bytes ?? 1)) * 100
          )
        )
      )
    : undefined;

  const statusPresentation = {
    pending: {
      icon: <Clock3 aria-hidden="true" size={14} />,
      label: 'Pending',
      className: 'text-muted-strong'
    },
    running: {
      icon: (
        <LoaderCircle aria-hidden="true" className="animate-spin" size={14} />
      ),
      label: 'Running',
      className: 'text-primary-hover'
    },
    canceling: {
      icon: (
        <LoaderCircle aria-hidden="true" className="animate-spin" size={14} />
      ),
      label: 'Canceling',
      className: 'text-warning'
    },
    canceled: {
      icon: <Ban aria-hidden="true" size={14} />,
      label: 'Canceled',
      className: 'text-muted-strong'
    },
    done: {
      icon: <CheckCircle2 aria-hidden="true" size={14} />,
      label: 'Complete',
      className: 'text-success'
    },
    error: {
      icon: <CircleAlert aria-hidden="true" size={14} />,
      label: 'Failed',
      className: 'text-danger'
    }
  }[progress.status];

  return (
    <div className="box-border w-full min-w-0 rounded-lg border border-border bg-surface-muted px-2 py-3 text-xs shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <div
          className={`inline-flex min-w-0 items-center gap-1.5 font-medium ${statusPresentation.className}`}
          role="status"
        >
          <span className="shrink-0">{statusPresentation.icon}</span>
          <span>{statusPresentation.label}</span>
          <span className="text-muted">· {progressLabel}</span>
        </div>
        {canCancel ? (
          <button
            aria-label="Cancel job"
            className="inline-flex shrink-0 items-center gap-1 rounded-md border border-border-strong bg-surface px-2 py-1 font-medium text-muted-strong transition-colors hover:border-danger-border hover:bg-danger-subtle hover:text-danger focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            onClick={() => void cancel()}
            title="Cancel job"
            type="button"
          >
            <X aria-hidden="true" size={13} />
            Cancel
          </button>
        ) : null}
      </div>

      <div
        aria-label={`${statusPresentation.label}: ${progressLabel}`}
        aria-valuemax={hasTotal ? 100 : undefined}
        aria-valuemin={hasTotal ? 0 : undefined}
        aria-valuenow={percentage}
        className={`mt-2 h-1.5 overflow-hidden rounded-full bg-border ${
          hasTotal ? '' : 'animate-pulse'
        }`}
        role="progressbar"
      >
        {hasTotal ? (
          <div
            className="h-full rounded-full bg-primary transition-[width] duration-300"
            style={{ width: `${percentage}%` }}
          />
        ) : null}
      </div>

      {progress.current_item ? (
        <div
          className="mt-2 truncate text-muted-strong"
          title={progress.current_item}
        >
          {progress.current_item}
        </div>
      ) : null}
      {progress.message ? (
        <div className="mt-1 text-muted">{progress.message}</div>
      ) : null}
    </div>
  );
};
