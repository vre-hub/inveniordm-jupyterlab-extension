import React from 'react';

import {
  JobProgressProps,
  useJobProgressUpdates
} from '../core/useJobProgressUpdates';

export const JobProgress: React.FC<JobProgressProps> = props => {
  const { progress, progressLabel, canCancel, cancel, loadingProgress } =
    useJobProgressUpdates(props);

  if (loadingProgress || !progress) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      {canCancel ? (
        <button onClick={cancel} type="button">
          Cancel job
        </button>
      ) : null}
      <progress
        value={progress.completed_bytes}
        max={progress.total_bytes ?? undefined}
      />
      <span>
        {progress.status} {progressLabel}
        {progress.current_item ? ` - ${progress.current_item}` : ''}
      </span>
      {progress.message ? <div>{progress.message}</div> : null}
    </div>
  );
};
