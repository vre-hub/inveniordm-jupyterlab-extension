import React from 'react';

import { ZenodoFileInfo } from './ZenodoFileInfo';

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
  id: string;
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
