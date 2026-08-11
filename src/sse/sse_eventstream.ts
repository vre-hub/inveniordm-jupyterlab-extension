import { ServerConnection } from '@jupyterlab/services';
import { subscribeToEvents, InvenioRDMEvent } from './sse_events';

type InvenioRDMEventListener = (event: InvenioRDMEvent) => void;

class SharedEventStream {
  private consecutiveNetworkFailures = 0;
  private controller: AbortController | null = null;
  private listeners = new Set<InvenioRDMEventListener>();
  private restartTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(private readonly serverSettings: ServerConnection.ISettings) {}

  subscribe(listener: InvenioRDMEventListener): () => void {
    this.listeners.add(listener);
    this.ensureConnected();

    return () => {
      this.listeners.delete(listener);
      if (this.listeners.size === 0) {
        this.controller?.abort();
        this.controller = null;
      }
    };
  }

  private ensureConnected(): void {
    if (this.controller !== null || this.restartTimer !== null) {
      return;
    }

    this.connect();
  }

  private connect(delayMs = 0): void {
    if (delayMs > 0) {
      this.restartTimer = setTimeout(() => {
        this.restartTimer = null;
        this.connect();
      }, delayMs);
      return;
    }

    if (this.listeners.size === 0) {
      return;
    }

    const controller = new AbortController();
    this.controller = controller;
    let retryDelayMs = 0;

    void subscribeToEvents(
      this.serverSettings,
      event => {
        this.dispatch(event);
      },
      controller.signal,
      () => {
        this.consecutiveNetworkFailures = 0;
      }
    )
      .catch(reason => {
        // Firefox can reject a pending response-body read with a TypeError
        // instead of an AbortError when the request is aborted. Check the
        // signal itself so intentional cleanup is not reported as a failure.
        if (controller.signal.aborted) {
          return;
        }

        retryDelayMs = 1000;
        if (reason instanceof ServerConnection.NetworkError) {
          this.consecutiveNetworkFailures += 1;
          if (this.consecutiveNetworkFailures === 3) {
            console.error('InvenioRDM event stream failed repeatedly.', reason);
          }
          return;
        }

        console.error('InvenioRDM event stream failed.', reason);
      })
      .finally(() => {
        if (this.controller !== controller) {
          return;
        }

        this.controller = null;
        if (this.listeners.size > 0) {
          this.connect(retryDelayMs);
        }
      });
  }

  private dispatch(event: InvenioRDMEvent): void {
    for (const listener of [...this.listeners]) {
      try {
        listener(event);
      } catch (error) {
        console.error('InvenioRDM event listener failed.', error);
      }
    }
  }
}

const sharedEventStreams = new WeakMap<
  ServerConnection.ISettings,
  SharedEventStream
>();

/**
 * Subscribe to InvenioRDM events through a shared SSE connection.
 */
export function subscribeToEventStream(
  serverSettings: ServerConnection.ISettings,
  listener: InvenioRDMEventListener
): () => void {
  let stream = sharedEventStreams.get(serverSettings);
  if (!stream) {
    stream = new SharedEventStream(serverSettings);
    sharedEventStreams.set(serverSettings, stream);
  }

  return stream.subscribe(listener);
}
