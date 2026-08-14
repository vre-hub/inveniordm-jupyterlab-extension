import React from 'react';
import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

import type { InsertInvenioRDMCellAction } from './jupyterlab_interactions';
import { requestAPI } from './request';
import { useEventData, useEventListener } from './sse';
import { useRemoteServerOverride, useServerSettings } from './store';
import { RemoteServerId } from './remoteServers';

/** Authentication state reported for a remote server. */
export type AccessTokenResponse = {
  access_token_present: boolean;
  access_token_valid: boolean;
  remote_server_id: RemoteServerId;
  remote_server_label: string;
  remote_server_base_url: string;
};

/** Authentication state or the error that prevented it from loading. */
export type AccessTokenStatus =
  | AccessTokenResponse
  | {
      error: string;
    };

/** Remote server metadata used in repository selectors. */
export type RemoteServerOption = {
  id: RemoteServerId;
  label: string;
  login_available: boolean;
};

/** Identifies the remote server currently used by API requests. */
export type CurrentRemoteServer = {
  id: RemoteServerId;
  display_name: string;
};

/** Lists the remote InvenioRDM servers available to the extension. */
export async function getRemoteServers(
  serverSettings: ServerConnection.ISettings
): Promise<RemoteServerOption[]> {
  return await requestAPI<RemoteServerOption[]>(
    'remote-servers',
    serverSettings
  );
}

/** Returns the configured default remote server. */
export async function getRemoteServersDefault(
  serverSettings: ServerConnection.ISettings
): Promise<RemoteServerOption> {
  return await requestAPI<RemoteServerOption>(
    'remote-servers/default',
    serverSettings
  );
}

/** Returns the remote server currently used by the backend. */
export async function getCurrentRemoteServer(
  serverSettings: ServerConnection.ISettings
): Promise<CurrentRemoteServer> {
  return await requestAPI<CurrentRemoteServer>(
    'remote-servers/current',
    serverSettings
  );
}

/** Tracks authentication status for the selected remote server. */
export function useAccessTokenStatus(): AccessTokenStatus | undefined {
  const serverSettings = useServerSettings();
  const remoteServerOverride = useRemoteServerOverride();
  const [state, setState] = React.useState<{
    remoteServerOverride: RemoteServerId | undefined;
    status: AccessTokenStatus;
  }>();
  const requestId = React.useRef(0);

  const updateStatus = React.useCallback(async (): Promise<void> => {
    const currentRequestId = ++requestId.current;
    try {
      const status = await requestAPI<AccessTokenResponse>(
        'access-token',
        serverSettings
      );
      if (currentRequestId === requestId.current) {
        setState({ remoteServerOverride, status });
      }
    } catch (reason) {
      if (currentRequestId === requestId.current) {
        setState({
          remoteServerOverride,
          status: { error: String(reason) }
        });
      }
    }
  }, [serverSettings, remoteServerOverride]);

  React.useEffect(() => {
    void updateStatus();
  }, [updateStatus]);

  useEventListener('auth.status.changed', () => {
    void updateStatus();
  });

  if (!state || state.remoteServerOverride !== remoteServerOverride) {
    return undefined;
  }
  return state.status;
}

/** Runs a callback when repository authentication status changes. */
export function useAccessTokenEventListener(onEvent: () => void): void {
  return useEventListener('auth.status.changed', onEvent);
}

/** Basic profile information for the authenticated user. */
export type InvenioRDMMeResponse = {
  email: string;
  id: number;
};

/** Returns basic profile information for the authenticated user. */
export async function getInvenioRDMMe(
  serverSettings: ServerConnection.ISettings
): Promise<InvenioRDMMeResponse> {
  return await requestAPI<InvenioRDMMeResponse>('me', serverSettings);
}

/** The download directory currently reported by the backend. */
export type SetInvenioRDMDownloadDirectoryResponse = {
  downloads_dir: string;
};

/** Returns the configured InvenioRDM download directory. */
export async function getInvenioRDMDownloadDirectory(
  serverSettings: ServerConnection.ISettings
): Promise<SetInvenioRDMDownloadDirectoryResponse> {
  return await requestAPI<SetInvenioRDMDownloadDirectoryResponse>(
    'settings/downloads-directory',
    serverSettings
  );
}

/** Changes the directory used for InvenioRDM downloads. */
export async function setInvenioRDMDownloadDirectory(
  serverSettings: ServerConnection.ISettings,
  downloadsDir: string
): Promise<SetInvenioRDMDownloadDirectoryResponse> {
  return await requestAPI<SetInvenioRDMDownloadDirectoryResponse>(
    'settings/downloads-directory',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ downloads_dir: downloadsDir })
    }
  );
}

/** Restores the default directory used for InvenioRDM downloads. */
export async function unsetInvenioRDMDownloadDirectory(
  serverSettings: ServerConnection.ISettings
): Promise<SetInvenioRDMDownloadDirectoryResponse> {
  return await requestAPI<SetInvenioRDMDownloadDirectoryResponse>(
    'settings/downloads-directory',
    serverSettings,
    { method: 'DELETE' }
  );
}

/**
 * Construct the URL for InvenioRDM authentication (login or logout),
 * with the correct return URL and remote server parameter.
 *
 * @param serverSettings - The server settings for the JupyterLab server.
 * @param action - The action to perform ('login' or 'logout').
 * @param returnTo - The URL to return to after authentication.
 * @param remoteServerId - The remote server to use.
 * @returns The constructed authentication URL.
 */
export function constructInvenioRDMAuthUrl(
  serverSettings: ServerConnection.ISettings,
  action: 'login' | 'logout',
  returnTo: string,
  remoteServerId?: RemoteServerId
): string {
  const params = new URLSearchParams({
    return_to: returnTo
  });

  if (remoteServerId) {
    params.set('remote_server', remoteServerId);
  }

  return (
    URLExt.join(
      serverSettings.baseUrl,
      'inveniordm-jupyterlab',
      'auth',
      action
    ) + `?${params.toString()}`
  );
}

/** Searches public records on the selected remote server. */
export async function searchInvenioRDMRecords(
  serverSettings: ServerConnection.ISettings,
  query: string,
  pagination: InvenioRDMPaginationParameters
): Promise<InvenioRDMRecordSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    include_files: 'true',
    page: pagination.page.toString(),
    size: pagination.size.toString()
  });
  return await requestAPI<InvenioRDMRecordSearchResponse>(
    `records?${params.toString()}`,
    serverSettings
  );
}

/** Returns a draft or published representation of a record. */
export async function getInvenioRDMRecordVariant(
  serverSettings: ServerConnection.ISettings,
  identifier: InvenioRDMRecordIdentifier
): Promise<InvenioRDMRecordData> {
  const params = new URLSearchParams({
    record_status: identifier.record_status
  });
  return await requestAPI<InvenioRDMRecordData>(
    `record-variants/${encodeURIComponent(identifier.record_id)}?${params.toString()}`,
    serverSettings
  );
}

/** Lists records owned by the authenticated user. */
export async function listInvenioRDMUserRecords(
  serverSettings: ServerConnection.ISettings,
  pagination: InvenioRDMPaginationParameters
): Promise<InvenioRDMRecordSearchResponse> {
  const params = new URLSearchParams({
    include_files: 'true',
    page: pagination.page.toString(),
    size: pagination.size.toString()
  });

  const queryString = params.toString();
  return await requestAPI<InvenioRDMRecordSearchResponse>(
    `user/records${queryString ? `?${queryString}` : ''}`,
    serverSettings
  );
}

/** Page selection supplied to paginated record endpoints. */
export type InvenioRDMPaginationParameters = {
  page: number;
  size: number;
};

/** Paginated record results returned by search and user listings. */
export type InvenioRDMRecordSearchResponse = {
  hits?: {
    hits?: InvenioRDMRecordData[];
    total?: number;
  };
  links?: Record<string, unknown>;
};

/** Basic record draft information returned after a mutation. */
export type InvenioRDMRecordDraftResponse = {
  id: string;
  links: {
    self_html: string;
    self?: string;
  };
  is_published?: boolean;
};

/** Discards a record draft owned by the authenticated user. */
export async function deleteInvenioRDMRecordDraft(
  serverSettings: ServerConnection.ISettings,
  recordId: string
): Promise<void> {
  await requestAPI<void>(
    `user/records/${encodeURIComponent(recordId)}`,
    serverSettings,
    { method: 'DELETE' }
  );
}

//TODO check if this is just InvenioRDMRecordData or if it is different
/** Summary of one version in a record's version history. */
export type InvenioRDMRecordVersion = {
  id: string;
  status: InvenioRDMRecordStatus;
  is_draft: boolean;
  parent?: {
    id?: string | null;
  };
  versions: {
    index: number;
  };
};

/** Lists the available versions of a record. */
export async function listInvenioRDMRecordVersions(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  includeDrafts: boolean
): Promise<InvenioRDMRecordVersion[]> {
  const params = new URLSearchParams({
    include_drafts: includeDrafts.toString()
  });
  return await requestAPI<InvenioRDMRecordVersion[]>(
    `records/${encodeURIComponent(recordId)}/versions?${params.toString()}`,
    serverSettings
  );
}

/** Draft created when a new record version is started. */
export type CreateInvenioRDMRecordVersionResponse = {
  draft: InvenioRDMRecordDraftResponse;
};

/** Creates a new draft version of a published record. */
export async function createInvenioRDMRecordVersion(
  serverSettings: ServerConnection.ISettings,
  recordId: string
): Promise<CreateInvenioRDMRecordVersionResponse> {
  return await requestAPI<CreateInvenioRDMRecordVersionResponse>(
    `records/${encodeURIComponent(recordId)}/versions`,
    serverSettings,
    { method: 'POST' }
  );
}

/** Identifier returned when a background job starts. */
export type StartJobResponse = {
  job_id: string;
};

/** Lifecycle state of an upload or download job. */
export type JobStatus =
  'pending' | 'running' | 'canceling' | 'canceled' | 'done' | 'error';

/** Output made available by a completed background job. */
export type JobResult = {
  draft?: InvenioRDMRecordDraftResponse;
  path?: string;
};

/** Current progress and result information for a background job. */
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

/** Job identifiers matching a backend query. */
export type FindJobsResponse = {
  job_ids: string[];
};

/** Identifies a draft or published record representation. */
export type InvenioRDMRecordIdentifier = {
  record_id: string;
  record_status: 'draft' | 'published';
};

/** Derive the identifier for a record's draft or published representation. */
export function inveniordmRecordIdentifierFromRecord(record: {
  id: string;
  is_draft: boolean;
}): InvenioRDMRecordIdentifier {
  return {
    record_id: record.id,
    record_status: record.is_draft ? 'draft' : 'published'
  };
}

/** Identifies a file within a draft or published record. */
export type InvenioRDMFileIdentifier = InvenioRDMRecordIdentifier & {
  file_key: string;
};

type ActiveJobIdentifier =
  | {
      jobType: 'upload';
      recordId: string;
    }
  | {
      jobType: 'download';
      fileId: InvenioRDMFileIdentifier;
    };

/** Returns the latest active job for an upload or file download. */
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

/** Starts creation of a record draft containing local files. */
export async function createInvenioRDMRecordDraftWithFiles(
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

/** Starts uploading local files to an existing record draft. */
export async function uploadInvenioRDMRecordFiles(
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

/** Identifies the record file deleted by the backend. */
export type DeleteInvenioRDMRecordFileResponse = {
  deleted_key: string;
};

/** Deletes a file from an InvenioRDM record draft. */
export async function deleteInvenioRDMRecordFile(
  serverSettings: ServerConnection.ISettings,
  fileId: InvenioRDMFileIdentifier
): Promise<DeleteInvenioRDMRecordFileResponse> {
  return await requestAPI<DeleteInvenioRDMRecordFileResponse>(
    `user/records/${encodeURIComponent(fileId.record_id)}/files`,
    serverSettings,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileId)
    }
  );
}

/** Returns live progress updates for a background job. */
export function useJobProgress(jobId: string) {
  return useEventData<JobProgressResponse | null>(
    `job.progress.${jobId}`,
    null
  );
}

/** Returns the latest known progress for a background job. */
export async function getJobProgress(
  serverSettings: ServerConnection.ISettings,
  jobId: string
): Promise<JobProgressResponse> {
  return await requestAPI<JobProgressResponse>(`jobs/${jobId}`, serverSettings);
}

/** Requests cancellation of a background job. */
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

/** Local availability and path of a remote file. */
export type InvenioRDMFileDownloadStatusResponse = {
  downloaded: boolean;
  path: string | null;
};

/** Result of removing a downloaded file from JupyterLab. */
export type DeleteInvenioRDMFileDownloadResponse = {
  deleted: boolean;
  path: string | null;
};

/** Starts downloading an InvenioRDM file into JupyterLab. */
export async function downloadInvenioRDMFile(
  serverSettings: ServerConnection.ISettings,
  fileId: InvenioRDMFileIdentifier
): Promise<StartJobResponse> {
  return await requestAPI<StartJobResponse>('files/download', serverSettings, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fileId)
  });
}

/** Returns whether an InvenioRDM file has been downloaded. */
export async function getInvenioRDMFileDownloadStatus(
  serverSettings: ServerConnection.ISettings,
  fileId: InvenioRDMFileIdentifier
): Promise<InvenioRDMFileDownloadStatusResponse> {
  return await requestAPI<InvenioRDMFileDownloadStatusResponse>(
    'files/status',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileId)
    }
  );
}

/** Removes a downloaded InvenioRDM file from JupyterLab. */
export async function deleteInvenioRDMFileDownload(
  serverSettings: ServerConnection.ISettings,
  fileId: InvenioRDMFileIdentifier
): Promise<DeleteInvenioRDMFileDownloadResponse> {
  return await requestAPI<DeleteInvenioRDMFileDownloadResponse>(
    'files/download',
    serverSettings,
    {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileId)
    }
  );
}

/** Returns the notebook cell action used to import a downloaded file. */
export async function getInvenioRDMFileImportCell(
  serverSettings: ServerConnection.ISettings,
  fileId: InvenioRDMFileIdentifier
): Promise<InsertInvenioRDMCellAction> {
  return await requestAPI<InsertInvenioRDMCellAction>(
    'files/import-cell',
    serverSettings,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileId)
    }
  );
}

/** Permission granted to the current user for a record. */
export type InvenioRDMRecordPermission = 'manage' | 'edit' | 'preview' | 'view';

/** Returns the current user's permission for a record representation. */
export async function getInvenioRDMRecordPermission(
  serverSettings: ServerConnection.ISettings,
  recordId: string,
  recordStatus: InvenioRDMFileIdentifier['record_status']
): Promise<InvenioRDMRecordPermission> {
  const params = new URLSearchParams({ record_status: recordStatus });
  return await requestAPI<InvenioRDMRecordPermission>(
    `records/${encodeURIComponent(recordId)}/permission?${params.toString()}`,
    serverSettings
  );
}

/** Tracks the current user's permission for a record representation. */
export function useInvenioRDMRecordPermission(
  id: string,
  recordStatus: InvenioRDMFileIdentifier['record_status']
): InvenioRDMRecordPermission | null {
  const serverSettings = useServerSettings();
  const [userPermission, setUserPermission] =
    React.useState<InvenioRDMRecordPermission | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    const fetchUserPermission = async () => {
      const permission = await getInvenioRDMRecordPermission(
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

/** Data sent when a record's draft or version history changes. */
export type InvenioRDMRecordVersionsChangedEventData = {
  type: 'version_created' | 'draft_discarded';
  record_id: string;
  discarded_draft_id?: string;
  parent_id?: string | null;
  record?: InvenioRDMRecordData;
  versions: InvenioRDMRecordVersion[];
};

/** Returns the available versions of a record. */
export function useInvenioRDMRecordVersions(
  recordId: string,
  includeDrafts: boolean
): InvenioRDMRecordVersion[] {
  const serverSettings = useServerSettings();
  const [versions, setVersions] = React.useState<InvenioRDMRecordVersion[]>([]);

  React.useEffect(() => {
    void listInvenioRDMRecordVersions(
      serverSettings,
      recordId,
      includeDrafts
    ).then((versions: InvenioRDMRecordVersion[]) => {
      const sortedVersions = versions.sort(
        (a, b) => a.versions.index - b.versions.index
      );
      setVersions(sortedVersions);
    });
  }, [includeDrafts, recordId, serverSettings]);

  return versions;
}

// TODO check if these fields exist/ if they are always present

/** File metadata included with an InvenioRDM record. */
export type InvenioRDMFile = {
  key: string;
  size?: number;
  links?: {
    content?: string;
    download?: string;
  };
};
type InvenioRDMRecordStatus =
  'new_version_draft' | 'draft' | 'published' | string;
// TODO check if these fields exist/ if they are always present

/** Record metadata used by the extension's record views. */
export type InvenioRDMRecordData = {
  id: string;
  is_draft: boolean;
  status: InvenioRDMRecordStatus;
  metadata?: {
    title?: string;
  };
  created: string; // format e.g. "2025-04-07T13:20:56.868888+00:00"
  updated: string;
  pids?: {
    doi?: {
      identifier?: string;
    };
  };
  files?: { entries?: Record<string, InvenioRDMFile>; count: number };
  links: {
    self_html: string;
  };
  versions: {
    is_latest: boolean;
  };
};
