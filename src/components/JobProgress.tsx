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
        className="inline-flex items-center gap-2 text-xs text-slate-500"
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
      className: 'text-slate-600'
    },
    running: {
      icon: (
        <LoaderCircle aria-hidden="true" className="animate-spin" size={14} />
      ),
      label: 'Running',
      className: 'text-blue-700'
    },
    canceling: {
      icon: (
        <LoaderCircle aria-hidden="true" className="animate-spin" size={14} />
      ),
      label: 'Canceling',
      className: 'text-amber-700'
    },
    canceled: {
      icon: <Ban aria-hidden="true" size={14} />,
      label: 'Canceled',
      className: 'text-slate-600'
    },
    done: {
      icon: <CheckCircle2 aria-hidden="true" size={14} />,
      label: 'Complete',
      className: 'text-emerald-700'
    },
    error: {
      icon: <CircleAlert aria-hidden="true" size={14} />,
      label: 'Failed',
      className: 'text-red-700'
    }
  }[progress.status];

  return (
    <div className="min-w-64 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div
          className={`inline-flex min-w-0 items-center gap-1.5 font-medium ${statusPresentation.className}`}
          role="status"
        >
          <span className="shrink-0">{statusPresentation.icon}</span>
          <span>{statusPresentation.label}</span>
          <span className="text-slate-500">· {progressLabel}</span>
        </div>
        {canCancel ? (
          <button
            aria-label="Cancel job"
            className="inline-flex shrink-0 items-center gap-1 rounded-md border border-slate-300 bg-white px-2 py-1 font-medium text-slate-600 transition-colors hover:border-red-200 hover:bg-red-50 hover:text-red-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
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
        className={`mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200 ${
          hasTotal ? '' : 'animate-pulse'
        }`}
        role="progressbar"
      >
        {hasTotal ? (
          <div
            className="h-full rounded-full bg-blue-600 transition-[width] duration-300"
            style={{ width: `${percentage}%` }}
          />
        ) : null}
      </div>

      {progress.current_item ? (
        <div
          className="mt-2 truncate text-slate-600"
          title={progress.current_item}
        >
          {progress.current_item}
        </div>
      ) : null}
      {progress.message ? (
        <div className="mt-1 text-slate-500">{progress.message}</div>
      ) : null}
    </div>
  );
};
