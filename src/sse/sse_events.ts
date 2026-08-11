import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

/**
 * Get the URL for the InvenioRDM extension SSE event stream.
 */
function eventSourceUrl(serverSettings: ServerConnection.ISettings): string {
  return URLExt.join(serverSettings.baseUrl, 'inveniordm-jupyterlab', 'events');
}

export type InvenioRDMEvent = {
  topic: string;
  data?: unknown;
};

/**
 * Subscribe to a InvenioRDM extension SSE event stream
 * and call onEvent for each event received.
 *
 * @param serverSettings - The server settings to use for the request.
 * @param onEvent - The callback to call for each event received.
 * @param signal - The AbortSignal to use for aborting the request.
 * @param onConnected - The callback to call once the response stream is open.
 * Passing an AbortSignal allows the caller to cancel the subscription when it is no longer needed.
 * @returns A promise that resolves when the subscription is established.
 */
export async function subscribeToEvents(
  serverSettings: ServerConnection.ISettings,
  onEvent: (event: InvenioRDMEvent) => void,
  signal: AbortSignal,
  onConnected?: () => void
): Promise<void> {
  const response = await ServerConnection.makeRequest(
    eventSourceUrl(serverSettings),
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

  onConnected?.();

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
  onEvent: (event: InvenioRDMEvent) => void
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
  onEvent: (event: InvenioRDMEvent) => void
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
