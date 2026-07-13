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

export async function listZenodoDepositions(
  serverSettings: ServerConnection.ISettings
): Promise<unknown> {
  const params = new URLSearchParams();
  params.append('include_files', 'true');

  const queryString = params.toString();
  return await requestAPI(
    `depositions${queryString ? `?${queryString}` : ''}`,
    serverSettings
  );
}

export type MinimalDepositionDraftResponse = {
  id: number;
  links?: {
    latest_draft_html?: string;
    self?: string;
  };
  title?: string;
  state?: string;
  submitted?: boolean;
};

export type StartJobResponse = {
  job_id: string;
};

export type JobStatus =
  'pending' | 'running' | 'canceling' | 'canceled' | 'done' | 'error';

export type JobResult = {
  deposition?: MinimalDepositionDraftResponse;
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
    depositionId: number;
    fileId?: string;
  }
): Promise<string | null> {
  const params = new URLSearchParams({
    job_type: options.jobType,
    deposition_id: String(options.depositionId),
    status: 'active',
    latest: 'true'
  });
  if (options.fileId !== undefined) {
    params.set('file_id', options.fileId);
  }

  const response = await requestAPI<FindJobsResponse>(
    `jobs?${params.toString()}`,
    serverSettings
  );
  return response.job_ids[0] ?? null;
}

export async function createMinimalDepositionDraft(
  serverSettings: ServerConnection.ISettings,
  filePaths: string[]
): Promise<StartJobResponse> {
  return await requestAPI<StartJobResponse>(
    'depositions/minimal-draft',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_paths: filePaths })
    }
  );
}

export async function uploadFilesToDeposition(
  serverSettings: ServerConnection.ISettings,
  depositionId: number,
  filePaths: string[]
): Promise<StartJobResponse> {
  return await requestAPI<StartJobResponse>(
    `depositions/${depositionId}/files`,
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_paths: filePaths })
    }
  );
}

export type DeleteZenodoDepositionFileResponse = {
  deposition: MinimalDepositionDraftResponse;
  deleted_key: string;
};

export async function deleteZenodoDepositionFile(
  serverSettings: ServerConnection.ISettings,
  depositionId: number,
  fileKey: string
): Promise<DeleteZenodoDepositionFileResponse> {
  return await requestAPI<DeleteZenodoDepositionFileResponse>(
    `depositions/${depositionId}/files`,
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
  depositionId: number,
  fileId: string
): Promise<StartJobResponse> {
  return await requestAPI<StartJobResponse>('files/download', serverSettings, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ deposition_id: depositionId, file_id: fileId })
  });
}

export async function getZenodoFileDownloadStatus(
  serverSettings: ServerConnection.ISettings,
  depositionId: number,
  fileId: string
): Promise<ZenodoFileDownloadStatusResponse> {
  return await requestAPI<ZenodoFileDownloadStatusResponse>(
    'files/status',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deposition_id: depositionId, file_id: fileId })
    }
  );
}

export async function deleteZenodoFileDownload(
  serverSettings: ServerConnection.ISettings,
  depositionId: number,
  fileId: string
): Promise<DeleteZenodoFileDownloadResponse> {
  return await requestAPI<DeleteZenodoFileDownloadResponse>(
    'files/download',
    serverSettings,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deposition_id: depositionId, file_id: fileId })
    }
  );
}

export async function getZenodoFileImportCell(
  serverSettings: ServerConnection.ISettings,
  depositionId: number,
  fileId: string
): Promise<InsertZenodoCellAction> {
  return await requestAPI<InsertZenodoCellAction>(
    'files/import-cell',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        deposition_id: depositionId,
        file_id: fileId
      })
    }
  );
}
