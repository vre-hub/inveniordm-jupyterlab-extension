import { ServerConnection } from '@jupyterlab/services';

import type { InsertZenodoCellAction } from './insertCell';
import { requestAPI } from './request';
import { useEventData } from './sse';

export type AccessTokenResponse = {
  access_token_present: boolean;
  access_token_valid: boolean;
  sandbox: boolean;
};

export function useAccessTokenStatus(): AccessTokenResponse | undefined {
  return useEventData<AccessTokenResponse | undefined>(
    'auth.status',
    undefined
  );
};

export type PutDeleteAccessTokenResponse = {
  message: string;
};

export type ZenodoMeResponse = {
  email: string;
  id: number;
};

export async function getZenodoMe(
  serverSettings: ServerConnection.ISettings
): Promise<ZenodoMeResponse> {
  return await requestAPI<ZenodoMeResponse>('me', serverSettings);
}

export async function putAccessToken(
  serverSettings: ServerConnection.ISettings,
  token: string
): Promise<PutDeleteAccessTokenResponse> {
  return await requestAPI('access-token', serverSettings, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ access_token: token })
  });
}

export async function deleteAccessToken(
  serverSettings: ServerConnection.ISettings
): Promise<PutDeleteAccessTokenResponse> {
  return await requestAPI('access-token', serverSettings, {
    method: 'DELETE'
  });
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

export async function getDownloadProgress(
  serverSettings: ServerConnection.ISettings,
  downloadId: string
): Promise<DownloadProgressResponse> {
  return await requestAPI<DownloadProgressResponse>(
    `files/downloads/${downloadId}/progress`,
    serverSettings
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
