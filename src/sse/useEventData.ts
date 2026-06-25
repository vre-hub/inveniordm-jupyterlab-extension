import React from "react";
import { useServerSettings } from "../store";
import { subscribeToEvents } from "./sse_events";

/**
 * Subscribe to a Zenodo extension SSE event topic and return the latest data for that topic.
 *
 * @param topic - The event topic to subscribe to.
 * @param initialData - The initial data to return before any events are received.
 * @returns The latest data for the specified event topic.
 */
export function useEventData<T>(topic: string, initialData: T): T {
  const serverSettings = useServerSettings();
  const [data, setData] = React.useState<T>(initialData);

  React.useEffect(() => {
    let isMounted = true;

    const controller = new AbortController();
    void subscribeToEvents(
      serverSettings,
      event => {
        if (!isMounted || event.topic !== topic) {
          return;
        }

        setData(event.data as T);
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

  return data;
}