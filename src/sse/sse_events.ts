import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

/**
* Get the URL for the Zenodo extension SSE event stream.
*/
function eventSourceUrl(
  serverSettings: ServerConnection.ISettings,
  topics: string[]
): string {
  const url = URLExt.join(
    serverSettings.baseUrl,
    'zenodo-jupyterlab',
    'events'
  );
  const params = new URLSearchParams();

  for (const topic of topics) {
    params.append('topic', topic);
  }

  return params.size > 0 ? `${url}?${params.toString()}` : url;
}

export type ZenodoEvent = {
  topic: string;
  data?: unknown;
};

/**
 * Subscribe to a Zenodo extension SSE event stream
 * and call onEvent for each event received.
 * 
 * @param serverSettings - The server settings to use for the request.
 * @param onEvent - The callback to call for each event received.
 * @param signal - The AbortSignal to use for aborting the request.
 * Passing an AbortSignal allows the caller to cancel the subscription when it is no longer needed.
 * @returns A promise that resolves when the subscription is established.
 */
export async function subscribeToEvents(
  serverSettings: ServerConnection.ISettings,
  topics: string[],
  onEvent: (event: ZenodoEvent) => void,
  signal: AbortSignal
): Promise<void> {
  const response = await ServerConnection.makeRequest(
    eventSourceUrl(serverSettings, topics),
    {
      cache: 'no-store',
      headers: { Accept: 'text/event-stream' },
      signal
    },
    serverSettings
  );

  if (!response.ok) {
    throw new ServerConnection.ResponseError(response);
  }

  if (!response.body) {
    throw new Error('The browser does not support streaming responses.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    buffer = parseEventBuffer(buffer, onEvent);
  }
}

function parseEventBuffer(
  buffer: string,
  onEvent: (event: ZenodoEvent) => void
): string {
  while (true) {
    const delimiter = buffer.match(/\r?\n\r?\n/);
    if (!delimiter || delimiter.index === undefined) {
      return buffer;
    }

    const rawEvent = buffer.slice(0, delimiter.index);
    buffer = buffer.slice(delimiter.index + delimiter[0].length);
    parseRawEvent(rawEvent, onEvent);
  }
}

function parseRawEvent(
  rawEvent: string,
  onEvent: (event: ZenodoEvent) => void
): void {
  let topic = 'message';
  const data: string[] = [];

  for (const line of rawEvent.split(/\r?\n/)) {
    if (line.startsWith(':')) {
      continue;
    }

    if (line.startsWith('event:')) {
      topic = line.slice('event:'.length).replace(/^\s+/, '');
    }

    if (line.startsWith('data:')) {
      data.push(line.slice('data:'.length).replace(/^\s+/, ''));
    }
  }

  onEvent({
    topic,
    data: data.length > 0 ? JSON.parse(data.join('\n')) : undefined
  });
}
