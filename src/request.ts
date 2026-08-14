import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

import { getRemoteServerOverride } from './store';

function withRemoteServerOverride(endPoint: string): string {
  const remoteServerOverride = getRemoteServerOverride();
  if (remoteServerOverride === undefined) {
    return endPoint;
  }

  const [path, queryString = ''] = endPoint.split('?');
  const params = new URLSearchParams(queryString);
  params.set('remote_server', remoteServerOverride);
  return `${path}?${params.toString()}`;
}

/**
 * Call the server extension
 *
 * @param endPoint API REST end point for the extension
 * @param serverSettings The server settings to use for the request
 * @param init Initial values for the request
 * @returns The response body interpreted as JSON
 */
export async function requestAPI<T>(
  endPoint: string,
  serverSettings: ServerConnection.ISettings,
  init: RequestInit = {}
): Promise<T> {
  const endPointWithRemoteServerOverride = withRemoteServerOverride(endPoint);
  // Make request to Jupyter API
  const requestUrl = URLExt.join(
    serverSettings.baseUrl,
    'inveniordm-jupyterlab', // our server extension's API namespace
    endPointWithRemoteServerOverride
  );

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(
      requestUrl,
      init,
      serverSettings
    );
  } catch (error) {
    throw new ServerConnection.NetworkError(error as any);
  }

  let data: any = await response.text();

  if (data.length > 0) {
    try {
      data = JSON.parse(data);
    } catch {
      console.log('Not a JSON response body.', response);
    }
  }

  if (!response.ok) {
    throw new ServerConnection.ResponseError(response, data.message || data);
  }

  return data;
}
