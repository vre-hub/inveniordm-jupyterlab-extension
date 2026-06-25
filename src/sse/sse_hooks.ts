import React from 'react';
import { useServerSettings } from '../store';
import { ZenodoEvent } from './sse_events';
import { subscribeToEventStream } from './sse_eventstream';

/**
 * Subscribe to a Zenodo extension SSE event topic and call onEvent for each event received.
 *
 * @param topic - The event topic to subscribe to.
 * @param onEvent - The callback to call for each event received.
 */
export function useEventListener(
  topic: string,
  onEvent: (event: ZenodoEvent) => void
): void {
  const serverSettings = useServerSettings();
  const onEventRef = React.useRef(onEvent);

  React.useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  React.useEffect(() => {
    let isMounted = true;

    const unsubscribe = subscribeToEventStream(serverSettings, event => {
      if (!isMounted || event.topic !== topic) {
        return;
      }

      onEventRef.current(event);
    });

    return () => {
      isMounted = false;
      unsubscribe();
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
