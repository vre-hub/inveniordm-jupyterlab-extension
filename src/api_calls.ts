import { ServerConnection } from '@jupyterlab/services';

import { requestAPI } from './request';


export type AccessTokenResponse = {
  access_token_present: boolean;
  access_token_valid: boolean;
};

export async function checkAccessStatus(
  serverSettings: ServerConnection.ISettings
): Promise<AccessTokenResponse> {
  return await requestAPI<AccessTokenResponse>('access-token', serverSettings);
}
