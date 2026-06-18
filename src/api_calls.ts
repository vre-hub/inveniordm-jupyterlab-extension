import { ServerConnection } from '@jupyterlab/services';

import { requestAPI } from './request';

export type AccessTokenResponse = {
  access_token_present: boolean;
  access_token_valid: boolean;
  sandbox: boolean;
};

export async function checkAccessStatus(
  serverSettings: ServerConnection.ISettings
): Promise<AccessTokenResponse> {
  return await requestAPI<AccessTokenResponse>('access-token', serverSettings);
}

export type PutDeleteAccessTokenResponse = {
  message: string;
};

export async function putAccessToken(
  serverSettings: ServerConnection.ISettings,
  token: string,
  sandbox: boolean
): Promise<PutDeleteAccessTokenResponse> {
  return await requestAPI('access-token', serverSettings, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ access_token: token, sandbox })
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
  query: string,
  options?: { sandbox: boolean }
): Promise<unknown> {
  const params = new URLSearchParams({ q: query });
  if (options?.sandbox !== undefined) {
    params.append('sandbox', options.sandbox.toString());
  }
  return await requestAPI(`records?${params.toString()}`, serverSettings);
}
