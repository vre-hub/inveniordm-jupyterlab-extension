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

export type CreateMinimalDepositionDraftResponse = {
  upload_id: string;
};

export type UploadProgressResponse = {
  status: 'pending' | 'running' | 'done' | 'error';
  bytes_uploaded: number;
  total_bytes: number;
  current_file: string | null;
  message: string | null;
  deposition: MinimalDepositionDraftResponse | null;
};

export async function createMinimalDepositionDraft(
  serverSettings: ServerConnection.ISettings,
  filePaths: string[]
): Promise<CreateMinimalDepositionDraftResponse> {
  return await requestAPI<CreateMinimalDepositionDraftResponse>(
    'depositions/minimal-draft',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_paths: filePaths })
    }
  );
}

export function useUploadProgress(uploadId: string) {
  return useEventData<UploadProgressResponse | null>(
    `upload.progress.${uploadId}`,
    null
  );
}

export async function getUploadProgress(
  serverSettings: ServerConnection.ISettings,
  uploadId: string
): Promise<UploadProgressResponse> {
  return await requestAPI<UploadProgressResponse>(
    `depositions/uploads/${uploadId}`,
    serverSettings
  );
}

export type DownloadZenodoFileResponse = {
  download_id: string;
};

export type DownloadProgressResponse = {
  status: 'pending' | 'running' | 'canceling' | 'canceled' | 'done' | 'error';
  bytes_downloaded: number;
  total_bytes: number | null;
  path: string | null;
  message: string | null;
  cancel_requested: boolean;
};

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
): Promise<DownloadZenodoFileResponse> {
  return await requestAPI<DownloadZenodoFileResponse>(
    'files/download',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deposition_id: depositionId, file_id: fileId })
    }
  );
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

export function useDownloadProgress(downloadId: string) {
  return useEventData<DownloadProgressResponse | null>(
    `download.progress.${downloadId}`,
    null
  );
}

export async function cancelDownload(
  serverSettings: ServerConnection.ISettings,
  downloadId: string
): Promise<DownloadProgressResponse> {
  return await requestAPI<DownloadProgressResponse>(
    `files/downloads/${downloadId}/cancel`,
    serverSettings,
    { method: 'POST' }
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
