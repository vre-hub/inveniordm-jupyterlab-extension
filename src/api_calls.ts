import React from 'react';
import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

import type { InsertZenodoCellAction } from './jupyterlab_interactions';
import { requestAPI } from './request';
import { useEventData, useEventListener } from './sse';
import { useServerSettings } from './store';

export type AccessTokenResponse = {
  access_token_present: boolean;
  access_token_valid: boolean;
  sandbox: boolean;
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
 * with the correct return URL and sandbox parameter.
 *
 * @param serverSettings - The server settings for the JupyterLab server.
 * @param action - The action to perform ('login' or 'logout').
 * @param returnTo - The URL to return to after authentication.
 * @param sandbox - Whether to use the Zenodo sandbox environment.
 * @returns The constructed authentication URL.
 */
export function constructZenodoAuthUrl(
  serverSettings: ServerConnection.ISettings,
  action: 'login' | 'logout',
  returnTo: string,
  sandbox: boolean = false
): string {
  const params = new URLSearchParams({
    return_to: returnTo,
    sandbox: sandbox.toString()
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
  const params = new URLSearchParams({ q: query });
  params.append('include_files', 'true');
  return await requestAPI(`records?${params.toString()}`, serverSettings);
}

export async function getZenodoRecord(
  serverSettings: ServerConnection.ISettings,
  recordId: string
): Promise<ZenodoRecordData> {
  return await requestAPI<ZenodoRecordData>(
    `records/${encodeURIComponent(recordId)}`,
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

export async function getZenodoUserRecord(
  serverSettings: ServerConnection.ISettings,
  recordId: string
): Promise<ZenodoRecordData> {
  return await requestAPI<ZenodoRecordData>(
    `user/records/${encodeURIComponent(recordId)}`,
    serverSettings
  );
}

export type ZenodoRecordVersion = {
  id: string;
  status: ZenodoRecordStatus;
  versions: {
    index: number;
  };
};

export async function listZenodoRecordVersions(
  serverSettings: ServerConnection.ISettings,
  recordId: string
): Promise<ZenodoRecordVersion[]> {
  return await requestAPI<ZenodoRecordVersion[]>(
    `records/${encodeURIComponent(recordId)}/versions`,
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

export async function getLatestActiveJobId(
  serverSettings: ServerConnection.ISettings,
  options: {
    jobType: 'upload' | 'download';
    recordId: string;
    fileKey?: string;
  }
): Promise<string | null> {
  const params = new URLSearchParams({
    job_type: options.jobType,
    record_id: String(options.recordId),
    status: 'active',
    latest: 'true'
  });
  if (options.fileKey !== undefined) {
    params.set('file_key', options.fileKey);
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
  draft: ZenodoRecordDraftResponse;
  deleted_key: string;
};

export async function deleteZenodoRecordFile(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  fileKey: string
): Promise<DeleteZenodoRecordFileResponse> {
  return await requestAPI<DeleteZenodoRecordFileResponse>(
    `user/records/${encodeURIComponent(recordId)}/files`,
    serverSettings,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: fileKey })
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
  recordId: string,
  fileKey: string
): Promise<StartJobResponse> {
  return await requestAPI<StartJobResponse>('files/download', serverSettings, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ record_id: recordId, file_key: fileKey })
  });
}

export async function getZenodoFileDownloadStatus(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  fileKey: string
): Promise<ZenodoFileDownloadStatusResponse> {
  return await requestAPI<ZenodoFileDownloadStatusResponse>(
    'files/status',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ record_id: recordId, file_key: fileKey })
    }
  );
}

export async function deleteZenodoFileDownload(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  fileKey: string
): Promise<DeleteZenodoFileDownloadResponse> {
  return await requestAPI<DeleteZenodoFileDownloadResponse>(
    'files/download',
    serverSettings,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ record_id: recordId, file_key: fileKey })
    }
  );
}

export async function getZenodoFileImportCell(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  fileKey: string
): Promise<InsertZenodoCellAction> {
  return await requestAPI<InsertZenodoCellAction>(
    'files/import-cell',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        record_id: recordId,
        file_key: fileKey
      })
    }
  );
}

export type ZenodoRecordPermission = 'manage' | 'edit' | 'preview' | 'view';

export async function getZenodoRecordPermission(
  serverSettings: ServerConnection.ISettings,
  recordId: string
): Promise<ZenodoRecordPermission> {
  return await requestAPI<ZenodoRecordPermission>(
    `records/${encodeURIComponent(recordId)}/permission`,
    serverSettings
  );
}

export function useZenodoRecordPermission(
  id: string
): ZenodoRecordPermission | null {
  const serverSettings = useServerSettings();
  const [userPermission, setUserPermission] =
    React.useState<ZenodoRecordPermission | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const fetchUserPermission = async () => {
      const permission = await getZenodoRecordPermission(serverSettings, id);
      if (isMounted) {
        setUserPermission(permission);
      }
    };

    void fetchUserPermission();

    return () => {
      isMounted = false;
    };
  }, [id, serverSettings]);

  return userPermission;
} // TODO check if these fields exist/ if they are always present

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
};
