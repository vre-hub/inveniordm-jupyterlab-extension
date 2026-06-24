import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

import { getSandboxOverride } from './store';

function withSandboxOverride(endPoint: string): string {
  const sandboxOverride = getSandboxOverride();
  if (sandboxOverride === undefined) {
    return endPoint;
  }

  const [path, queryString = ''] = endPoint.split('?');
  const params = new URLSearchParams(queryString);
  params.set('sandbox', sandboxOverride.toString());
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
  const endPointWithSandboxOverride = withSandboxOverride(endPoint);
  // Make request to Jupyter API
  const requestUrl = URLExt.join(
    serverSettings.baseUrl,
    'zenodo-jupyterlab', // our server extension's API namespace
    endPointWithSandboxOverride
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
    } catch (error) {
      console.log('Not a JSON response body.', response);
    }
  }

  if (!response.ok) {
    throw new ServerConnection.ResponseError(response, data.message || data);
  }

  return data;
}
