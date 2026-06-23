import React from 'react';
import { ServerConnection } from '@jupyterlab/services';

import { downloadZenodoFile } from '../api_calls';

export type ZenodoFile = {
  id?: string;
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
  serverSettings: ServerConnection.ISettings;
}> = ({ file, serverSettings }) => {
  const filename = file.key ?? file.filename ?? file.id ?? 'download';
  const download = async (): Promise<void> => {
    if (!file.links?.content) {
      return;
    }
    await downloadZenodoFile(serverSettings, file.links.content, filename);
  };

  return (
    <div>
      <div>
        {filename}
        {/* TODO display file size in a reasonable unit */}
        {file.size ? ` (${(file.size / 1024 / 1024).toFixed(2)} MB)` : null}
      </div>
      <button disabled={!file.links?.content} onClick={download} type="button">
        Download in JupyterServer
      </button>
    </div>
  );
};

export const ZenodoResource: React.FC<{
  resource: ZenodoResourceData;
  serverSettings: ServerConnection.ISettings;
}> = ({ resource, serverSettings }) => (
  <section>
    <h4>{resource.title ?? resource.metadata?.title ?? resource.id}</h4>
    <div>ID: {resource.id}</div>
    {resource.doi ? <div>DOI: {resource.doi}</div> : null}
    {resource.state ? <div>State: {resource.state}</div> : null}
    <div>
      {getFiles(resource.files).map(file => (
        <ZenodoFileInfo
          file={file}
          key={file.id ?? file.key ?? file.filename}
          serverSettings={serverSettings}
        />
      ))}
    </div>
  </section>
);
