import React from 'react';

import { downloadZenodoFile, getZenodoFileImportCell } from '../api_calls';
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

export const ZenodoFileInfo: React.FC<{
  file: ZenodoFile;
  depositionId: number;
}> = ({ file, depositionId }) => {
  const serverSettings = useServerSettings();
  const insertZenodoCell = useInsertZenodoCell();
  const filename = file.key ?? file.filename ?? file.id ?? 'download';
  const fileId = file.file_id;
  const download = async (): Promise<void> => {
    await downloadZenodoFile(serverSettings, depositionId, fileId);
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
