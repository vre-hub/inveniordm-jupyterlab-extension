import React from "react";
import { useServerSettings } from "../store";
import { subscribeToEvents } from "./sse_events";

/**
 * Subscribe to a Zenodo extension SSE event topic and call onEvent for each event received.
 *
 * @param topic - The event topic to subscribe to.
 * @param onEvent - The callback to call for each event received.
 */
export function useEventListener(
  topic: string,
  onEvent: (event: any) => void
): void {
  const serverSettings = useServerSettings();

  React.useEffect(() => {
    let isMounted = true;

    const controller = new AbortController();
    void subscribeToEvents(
      serverSettings,
      event => {
        if (!isMounted || event.topic !== topic) {
          return;
        }

        onEvent(event);
      },
      controller.signal
    ).catch(reason => {
      if (isMounted && reason.name !== 'AbortError') {
        console.error('Zenodo event stream failed.', reason);
      }
    });

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [serverSettings, topic]);

}

/**
 * Subscribe to a Zenodo extension SSE event topic and return the latest data for that topic.
 *
 * @param topic - The event topic to subscribe to.
 * @param initialData - The initial data to return before any events are received.
 * @returns The latest data for the specified event topic.
 */
export function useEventData<T>(topic: string, initialData: T): T {
  const [data, setData] = React.useState<T>(initialData);

  useEventListener(topic, event => {
    setData(event.data as T);
  });

  return data;
}