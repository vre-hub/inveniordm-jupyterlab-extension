import React from 'react';

export type ZenodoFile = {
  id?: string;
  key?: string;
  filename?: string;
  size?: number;
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

export const ZenodoFileInfo: React.FC<{ file: ZenodoFile }> = ({ file }) => (
  <li>
    {file.filename ?? file.key ?? file.id ?? 'Untitled file'}
    {/* TODO display file size in a reasonable unit */}
    {file.size ? ` (${(file.size / 1024 / 1024).toFixed(2)} MB)` : null}
  </li>
);

export const ZenodoResource: React.FC<{ resource: ZenodoResourceData }> = ({
  resource
}) => (
  <section>
    <h4>{resource.title ?? resource.metadata?.title ?? resource.id}</h4>
    <div>ID: {resource.id}</div>
    {resource.doi ? <div>DOI: {resource.doi}</div> : null}
    {resource.state ? <div>State: {resource.state}</div> : null}
    <ul>
      {getFiles(resource.files).map(file => (
        <ZenodoFileInfo file={file} key={file.id ?? file.key ?? file.filename} />
      ))}
    </ul>
  </section>
);
