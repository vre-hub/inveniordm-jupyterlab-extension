import React from 'react';
import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

import type { InsertZenodoCellAction } from './jupyterlab_interactions';
import { requestAPI } from './request';
import { useEventData, useEventListener } from './sse';
import { useServerSettings } from './store';
import { RemoteServerId } from './remoteServers';

export type AccessTokenResponse = {
  access_token_present: boolean;
  access_token_valid: boolean;
  remote_server_id: RemoteServerId;
};

export function useAccessTokenStatus(): AccessTokenResponse | undefined {
  const serverSettings = useServerSettings();
  const [status, setStatus] = React.useState<AccessTokenResponse>();

  const updateStatus = React.useCallback(async (): Promise<void> => {
    setStatus(
      await await requestAPI<AccessTokenResponse>(
        'access-token',
        serverSettings
      )
    );
  }, [serverSettings]);

  React.useEffect(() => {
    void updateStatus();
  }, [updateStatus]);

  useEventListener('auth.status.changed', () => {
    void updateStatus();
  });

  return status;
}

export function useAccessTokenEventListener(onEvent: () => void): void {
  return useEventListener('auth.status.changed', onEvent);
}

export type ZenodoMeResponse = {
  email: string;
  id: number;
};

export async function getZenodoMe(
  serverSettings: ServerConnection.ISettings
): Promise<ZenodoMeResponse> {
  return await requestAPI<ZenodoMeResponse>('me', serverSettings);
}

export type SetZenodoDownloadDirectoryResponse = {
  downloads_dir: string;
};

export async function getZenodoDownloadDirectory(
  serverSettings: ServerConnection.ISettings
): Promise<SetZenodoDownloadDirectoryResponse> {
  return await requestAPI<SetZenodoDownloadDirectoryResponse>(
    'settings/downloads-directory',
    serverSettings
  );
}

export async function setZenodoDownloadDirectory(
  serverSettings: ServerConnection.ISettings,
  downloadsDir: string
): Promise<SetZenodoDownloadDirectoryResponse> {
  return await requestAPI<SetZenodoDownloadDirectoryResponse>(
    'settings/downloads-directory',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ downloads_dir: downloadsDir })
    }
  );
}

export async function unsetZenodoDownloadDirectory(
  serverSettings: ServerConnection.ISettings
): Promise<SetZenodoDownloadDirectoryResponse> {
  return await requestAPI<SetZenodoDownloadDirectoryResponse>(
    'settings/downloads-directory',
    serverSettings,
    { method: 'DELETE' }
  );
}

/**
 * Construct the URL for Zenodo authentication (login or logout),
 * with the correct return URL and remote server parameter.
 *
 * @param serverSettings - The server settings for the JupyterLab server.
 * @param action - The action to perform ('login' or 'logout').
 * @param returnTo - The URL to return to after authentication.
 * @param remoteServerId - The remote server to use.
 * @returns The constructed authentication URL.
 */
export function constructZenodoAuthUrl(
  serverSettings: ServerConnection.ISettings,
  action: 'login' | 'logout',
  returnTo: string,
  remoteServerId: RemoteServerId = RemoteServerId.ZenodoProduction
): string {
  const params = new URLSearchParams({
    return_to: returnTo,
    remote_server: remoteServerId
  });
  return (
    URLExt.join(serverSettings.baseUrl, 'zenodo-jupyterlab', 'auth', action) +
    `?${params.toString()}`
  );
}

export async function searchZenodoRecords(
  serverSettings: ServerConnection.ISettings,
  query: string
): Promise<unknown> {
  const params = new URLSearchParams({ q: query, include_files: 'true' });
  return await requestAPI(`records?${params.toString()}`, serverSettings);
}

export async function getZenodoRecordVariant(
  serverSettings: ServerConnection.ISettings,
  identifier: ZenodoRecordIdentifier
): Promise<ZenodoRecordData> {
  const params = new URLSearchParams({
    record_status: identifier.record_status
  });
  return await requestAPI<ZenodoRecordData>(
    `record-variants/${encodeURIComponent(identifier.record_id)}?${params.toString()}`,
    serverSettings
  );
}

export async function listZenodoUserRecords(
  serverSettings: ServerConnection.ISettings
): Promise<unknown> {
  const params = new URLSearchParams();
  params.append('include_files', 'true');

  const queryString = params.toString();
  return await requestAPI(
    `user/records${queryString ? `?${queryString}` : ''}`,
    serverSettings
  );
}

export type ZenodoRecordDraftResponse = {
  id: string;
  links: {
    self_html: string;
    self?: string;
  };
  is_published?: boolean;
};

export async function deleteZenodoRecordDraft(
  serverSettings: ServerConnection.ISettings,
  recordId: string
): Promise<void> {
  await requestAPI<void>(
    `user/records/${encodeURIComponent(recordId)}`,
    serverSettings,
    { method: 'DELETE' }
  );
}

//TODO check if this is just ZenodoRecordData or if it is different
export type ZenodoRecordVersion = {
  id: string;
  status: ZenodoRecordStatus;
  is_draft: boolean;
  parent?: {
    id?: string | null;
  };
  versions: {
    index: number;
  };
};

export async function listZenodoRecordVersions(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  includeDrafts: boolean
): Promise<ZenodoRecordVersion[]> {
  const params = new URLSearchParams({
    include_drafts: includeDrafts.toString()
  });
  return await requestAPI<ZenodoRecordVersion[]>(
    `records/${encodeURIComponent(recordId)}/versions?${params.toString()}`,
    serverSettings
  );
}

export type CreateZenodoRecordVersionResponse = {
  draft: ZenodoRecordDraftResponse;
};

export async function createZenodoRecordVersion(
  serverSettings: ServerConnection.ISettings,
  recordId: string
): Promise<CreateZenodoRecordVersionResponse> {
  return await requestAPI<CreateZenodoRecordVersionResponse>(
    `records/${encodeURIComponent(recordId)}/versions`,
    serverSettings,
    { method: 'POST' }
  );
}

export type StartJobResponse = {
  job_id: string;
};

export type JobStatus =
  'pending' | 'running' | 'canceling' | 'canceled' | 'done' | 'error';

export type JobResult = {
  draft?: ZenodoRecordDraftResponse;
  path?: string;
};

export type JobProgressResponse = {
  job_id: string;
  job_type: 'upload' | 'download';
  status: JobStatus;
  completed_bytes: number;
  total_bytes: number | null;
  current_item: string | null;
  message: string | null;
  result: JobResult | null;
  cancel_requested: boolean;
};

export type FindJobsResponse = {
  job_ids: string[];
};

export type ZenodoRecordIdentifier = {
  record_id: string;
  record_status: 'draft' | 'published';
};

/** Derive the identifier for a record's draft or published representation. */
export function zenodoRecordIdentifierFromRecord(record: {
  id: string;
  is_draft: boolean;
}): ZenodoRecordIdentifier {
  return {
    record_id: record.id,
    record_status: record.is_draft ? 'draft' : 'published'
  };
}

export type ZenodoFileIdentifier = ZenodoRecordIdentifier & {
  file_key: string;
};

type ActiveJobIdentifier =
  | {
      jobType: 'upload';
      recordId: string;
    }
  | {
      jobType: 'download';
      fileId: ZenodoFileIdentifier;
    };

export async function getLatestActiveJobId(
  serverSettings: ServerConnection.ISettings,
  identifier: ActiveJobIdentifier
): Promise<string | null> {
  const recordId =
    identifier.jobType === 'download'
      ? identifier.fileId.record_id
      : identifier.recordId;
  const params = new URLSearchParams({
    job_type: identifier.jobType,
    record_id: recordId,
    status: 'active',
    latest: 'true'
  });
  if (identifier.jobType === 'download') {
    params.set('file_key', identifier.fileId.file_key);
    params.set('record_status', identifier.fileId.record_status);
  }

  const response = await requestAPI<FindJobsResponse>(
    `jobs?${params.toString()}`,
    serverSettings
  );
  return response.job_ids[0] ?? null;
}

export async function createZenodoRecordDraftWithFiles(
  serverSettings: ServerConnection.ISettings,
  filePaths: string[]
): Promise<StartJobResponse> {
  return await requestAPI<StartJobResponse>(
    'user/records/draft-with-files',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_paths: filePaths })
    }
  );
}

export async function uploadZenodoRecordFiles(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  filePaths: string[]
): Promise<StartJobResponse> {
  return await requestAPI<StartJobResponse>(
    `user/records/${encodeURIComponent(recordId)}/files`,
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_paths: filePaths })
    }
  );
}

export type DeleteZenodoRecordFileResponse = {
  deleted_key: string;
};

export async function deleteZenodoRecordFile(
  serverSettings: ServerConnection.ISettings,
  fileId: ZenodoFileIdentifier
): Promise<DeleteZenodoRecordFileResponse> {
  return await requestAPI<DeleteZenodoRecordFileResponse>(
    `user/records/${encodeURIComponent(fileId.record_id)}/files`,
    serverSettings,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileId)
    }
  );
}

export function useJobProgress(jobId: string) {
  return useEventData<JobProgressResponse | null>(
    `job.progress.${jobId}`,
    null
  );
}

export async function getJobProgress(
  serverSettings: ServerConnection.ISettings,
  jobId: string
): Promise<JobProgressResponse> {
  return await requestAPI<JobProgressResponse>(`jobs/${jobId}`, serverSettings);
}

export async function cancelJob(
  serverSettings: ServerConnection.ISettings,
  jobId: string
): Promise<JobProgressResponse> {
  return await requestAPI<JobProgressResponse>(
    `jobs/${jobId}/cancel`,
    serverSettings,
    { method: 'POST' }
  );
}

export type ZenodoFileDownloadStatusResponse = {
  downloaded: boolean;
  path: string | null;
};

export type DeleteZenodoFileDownloadResponse = {
  deleted: boolean;
  path: string | null;
};

export async function downloadZenodoFile(
  serverSettings: ServerConnection.ISettings,
  fileId: ZenodoFileIdentifier
): Promise<StartJobResponse> {
  return await requestAPI<StartJobResponse>('files/download', serverSettings, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fileId)
  });
}

export async function getZenodoFileDownloadStatus(
  serverSettings: ServerConnection.ISettings,
  fileId: ZenodoFileIdentifier
): Promise<ZenodoFileDownloadStatusResponse> {
  return await requestAPI<ZenodoFileDownloadStatusResponse>(
    'files/status',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileId)
    }
  );
}

export async function deleteZenodoFileDownload(
  serverSettings: ServerConnection.ISettings,
  fileId: ZenodoFileIdentifier
): Promise<DeleteZenodoFileDownloadResponse> {
  return await requestAPI<DeleteZenodoFileDownloadResponse>(
    'files/download',
    serverSettings,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileId)
    }
  );
}

export async function getZenodoFileImportCell(
  serverSettings: ServerConnection.ISettings,
  fileId: ZenodoFileIdentifier
): Promise<InsertZenodoCellAction> {
  return await requestAPI<InsertZenodoCellAction>(
    'files/import-cell',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileId)
    }
  );
}

export type ZenodoRecordPermission = 'manage' | 'edit' | 'preview' | 'view';

export async function getZenodoRecordPermission(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  recordStatus: ZenodoFileIdentifier['record_status']
): Promise<ZenodoRecordPermission> {
  const params = new URLSearchParams({ record_status: recordStatus });
  return await requestAPI<ZenodoRecordPermission>(
    `records/${encodeURIComponent(recordId)}/permission?${params.toString()}`,
    serverSettings
  );
}

export function useZenodoRecordPermission(
  id: string,
  recordStatus: ZenodoFileIdentifier['record_status']
): ZenodoRecordPermission | null {
  const serverSettings = useServerSettings();
  const [userPermission, setUserPermission] =
    React.useState<ZenodoRecordPermission | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const fetchUserPermission = async () => {
      const permission = await getZenodoRecordPermission(
        serverSettings,
        id,
        recordStatus
      );
      if (isMounted) {
        setUserPermission(permission);
      }
    };

    void fetchUserPermission();

    return () => {
      isMounted = false;
    };
  }, [id, recordStatus, serverSettings]);

  return userPermission;
}

export type ZenodoRecordVersionsChangedEventData = {
  type: 'version_created' | 'draft_discarded';
  record_id: string;
  discarded_draft_id?: string;
  parent_id?: string | null;
  record?: ZenodoRecordData;
  versions: ZenodoRecordVersion[];
};

export function useZenodoRecordVersions(
  recordId: string,
  includeDrafts: boolean
): ZenodoRecordVersion[] {
  const serverSettings = useServerSettings();
  const [versions, setVersions] = React.useState<ZenodoRecordVersion[]>([]);

  React.useEffect(() => {
    void listZenodoRecordVersions(serverSettings, recordId, includeDrafts).then(
      (versions: ZenodoRecordVersion[]) => {
        const sortedVersions = versions.sort(
          (a, b) => a.versions.index - b.versions.index
        );
        setVersions(sortedVersions);
      }
    );
  }, [includeDrafts, recordId, serverSettings]);

  return versions;
}

// TODO check if these fields exist/ if they are always present

export type ZenodoFile = {
  key: string;
  size?: number;
  links?: {
    content?: string;
    download?: string;
  };
};
type ZenodoRecordStatus = 'new_version_draft' | 'draft' | 'published';
// TODO check if these fields exist/ if they are always present

export type ZenodoRecordData = {
  id: string;
  is_draft: boolean;
  status: ZenodoRecordStatus;
  metadata?: {
    title?: string;
  };
  pids?: {
    doi?: {
      identifier?: string;
    };
  };
  files?: { entries?: Record<string, ZenodoFile> };
  links: {
    self_html: string;
  };
  versions: {
    is_latest: boolean;
  };
};
