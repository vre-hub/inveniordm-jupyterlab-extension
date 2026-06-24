import React from 'react';

import {
  cancelDownload,
  downloadZenodoFile,
  DownloadProgressResponse,
  getDownloadProgress,
  getZenodoFileImportCell
} from '../api_calls';
import { useInsertZenodoCell, useServerSettings } from '../store';

export type ZenodoFile = {
  id?: string;
  file_id: string;
  key?: string;
  filename?: string;
  size?: number;
  links?: {
    content?: string;
  };
};

export type ZenodoResourceData = {
  id: number;
  doi?: string;
  title?: string;
  state?: string;
  metadata?: {
    title?: string;
  };
  files?: ZenodoFile[] | { entries?: ZenodoFile[] };
};

const getFiles = (files: ZenodoResourceData['files']): ZenodoFile[] => {
  if (Array.isArray(files)) {
    return files;
  }
  return files?.entries ?? [];
};

const ZenodoDownloadProgress: React.FC<{
  downloadId: string;
}> = ({ downloadId }) => {
  const serverSettings = useServerSettings();
  const [progress, setProgress] =
    React.useState<DownloadProgressResponse | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const poll = async (): Promise<void> => {
      const nextProgress = await getDownloadProgress(serverSettings, downloadId);
      if (!isMounted) {
        return;
      }
      setProgress(nextProgress);
      if (
        nextProgress.status === 'done' ||
        nextProgress.status === 'canceled' ||
        nextProgress.status === 'error'
      ) {
        window.clearInterval(interval);
      }
    };

    setProgress({
      status: 'pending',
      bytes_downloaded: 0,
      total_bytes: null,
      path: null,
      message: null,
      cancel_requested: false
    });
    const interval = window.setInterval(poll, 500);
    poll();

    return () => {
      isMounted = false;
      window.clearInterval(interval);
    };
  }, [downloadId, serverSettings]);

  const cancel = async (): Promise<void> => {
    setProgress(await cancelDownload(serverSettings, downloadId));
  };
  const progressLabel =
    progress?.total_bytes && progress.total_bytes > 0
      ? `${Math.round((progress.bytes_downloaded / progress.total_bytes) * 100)}%`
      : progress
        ? `${progress.bytes_downloaded} bytes`
        : null;
  const canCancel =
    progress !== null &&
    (progress.status === 'pending' || progress.status === 'running');

  if (progress === null) {
    return null;
  }

  return (
    <div>
      {canCancel ? (
        <button onClick={cancel} type="button">
          Cancel download
        </button>
      ) : null}
      <progress
        value={progress.bytes_downloaded}
        max={progress.total_bytes ?? undefined}
      />
      <span>
        {progress.status} {progressLabel}
      </span>
      {progress.message ? <div>{progress.message}</div> : null}
    </div>
  );
};

export const ZenodoFileInfo: React.FC<{
  file: ZenodoFile;
  depositionId: number;
}> = ({ file, depositionId }) => {
  const serverSettings = useServerSettings();
  const insertZenodoCell = useInsertZenodoCell();
  const [downloadId, setDownloadId] = React.useState<string | null>(null);
  const filename = file.key ?? file.filename ?? file.id ?? 'download';
  const fileId = file.file_id

  const download = async (): Promise<void> => {
    const response = await downloadZenodoFile(
      serverSettings,
      depositionId,
      fileId
    );
    setDownloadId(response.download_id);
  };
  const insertImportCell = async (): Promise<void> => {
    insertZenodoCell(
      await getZenodoFileImportCell(serverSettings, depositionId, fileId)
    );
  };

  return (
    <div>
      <div>
        {filename}
        {/* TODO display file size in a reasonable unit */}
        {file.size ? ` (${(file.size / 1024 / 1024).toFixed(2)} MB)` : null}
      </div>
      <button disabled={!fileId} onClick={download} type="button">
        Download in JupyterServer
      </button>
      <button disabled={!fileId} onClick={insertImportCell} type="button">
        Insert import cell
      </button>
      {downloadId ? <ZenodoDownloadProgress downloadId={downloadId} /> : null}
    </div>
  );
};

export const ZenodoResource: React.FC<{
  resource: ZenodoResourceData;
}> = ({ resource }) => {
  return (
    <section>
      <h4>{resource.title ?? resource.metadata?.title ?? resource.id}</h4>
      <div>ID: {resource.id}</div>
      {resource.doi ? <div>DOI: {resource.doi}</div> : null}
      {resource.state ? <div>State: {resource.state}</div> : null}
      <div>
        {getFiles(resource.files).map(file => (
          <ZenodoFileInfo
            file={file}
            key={file.file_id ?? file.id ?? file.key ?? file.filename}
            depositionId={resource.id}
          />
        ))}
      </div>
    </section>
  );
};
