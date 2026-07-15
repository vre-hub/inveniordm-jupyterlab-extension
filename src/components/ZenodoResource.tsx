import React from 'react';

import { ZenodoFileInfo } from './ZenodoFileInfo';
import { EditRecordButton } from './EditRecordButton';

export type ZenodoFile = {
  key: string;
  size?: number;
  links?: {
    content?: string;
    download?: string;
  };
};

export type ZenodoResourceData = {
  id: string;
  status: string;
  metadata?: {
    title?: string;
  };
  pids?: {
    doi?: {
      identifier?: string;
    };
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
      <h4>{resource.metadata?.title ?? resource.id}</h4>
      <div>ID: {resource.id}</div>
      {resource.pids?.doi?.identifier ? (
        <div>DOI: {resource.pids.doi.identifier}</div>
      ) : null}
      <div>Status: {resource.status}</div>
      <div>
        {getFiles(resource.files).map(file => (
          <ZenodoFileInfo file={file} key={file.key} recordId={resource.id} />
        ))}
      </div>
      <EditRecordButton id={resource.id} />
    </section>
  );
};
