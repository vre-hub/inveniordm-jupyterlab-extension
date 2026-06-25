import { ServerConnection } from "@jupyterlab/services";
import { subscribeToEvents, ZenodoEvent } from "./sse_events";

type ZenodoEventListener = (event: ZenodoEvent) => void;

class SharedEventStream {
  private controller: AbortController | null = null;
  private listeners = new Set<ZenodoEventListener>();
  private restartTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(private readonly serverSettings: ServerConnection.ISettings) {}

  subscribe(listener: ZenodoEventListener): () => void {
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
      controller.signal
    )
      .catch(reason => {
        if (reason?.name === 'AbortError') {
          return;
        }

        retryDelayMs = 1000;
        console.error('Zenodo event stream failed.', reason);
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

  private dispatch(event: ZenodoEvent): void {
    for (const listener of [...this.listeners]) {
      try {
        listener(event);
      } catch (error) {
        console.error('Zenodo event listener failed.', error);
      }
    }
  }
}

const sharedEventStreams = new WeakMap<
  ServerConnection.ISettings,
  SharedEventStream
>();

/**
 * Subscribe to Zenodo events through a shared SSE connection.
 */
export function subscribeToEventStream(
  serverSettings: ServerConnection.ISettings,
  listener: ZenodoEventListener
): () => void {
  let stream = sharedEventStreams.get(serverSettings);
  if (!stream) {
    stream = new SharedEventStream(serverSettings);
    sharedEventStreams.set(serverSettings, stream);
  }

  return stream.subscribe(listener);
}
