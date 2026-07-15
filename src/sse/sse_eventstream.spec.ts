import { ServerConnection } from '@jupyterlab/services';
import * as sseEvents from './sse_events';
import { subscribeToEventStream } from './sse_eventstream';

describe('subscribeToEventStream', () => {
  afterEach(() => {
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  it('does not report Firefox response-body errors caused by aborting', async () => {
    jest.spyOn(sseEvents, 'subscribeToEvents').mockImplementation(
      (_serverSettings, _onEvent, signal) =>
        new Promise((_resolve, reject) => {
          signal.addEventListener(
            'abort',
            () => reject(new TypeError('Error in input stream')),
            { once: true }
          );
        })
    );
    const consoleError = jest
      .spyOn(console, 'error')
      .mockImplementation(() => undefined);
    const serverSettings = ServerConnection.makeSettings();

    const unsubscribe = subscribeToEventStream(serverSettings, () => undefined);
    unsubscribe();
    await Promise.resolve();
    await Promise.resolve();

    expect(consoleError).not.toHaveBeenCalled();
  });

  it('retries an isolated network failure without reporting it', async () => {
    jest.useFakeTimers();
    const subscribe = jest
      .spyOn(sseEvents, 'subscribeToEvents')
      .mockRejectedValueOnce(
        new ServerConnection.NetworkError(
          new TypeError('NetworkError when attempting to fetch resource')
        )
      )
      .mockImplementation((_serverSettings, _onEvent, signal, onConnected) => {
        onConnected?.();
        return new Promise((_resolve, reject) => {
          signal.addEventListener(
            'abort',
            () => reject(new DOMException('Aborted', 'AbortError')),
            { once: true }
          );
        });
      });
    const consoleError = jest
      .spyOn(console, 'error')
      .mockImplementation(() => undefined);
    const serverSettings = ServerConnection.makeSettings();
    const unsubscribe = subscribeToEventStream(serverSettings, () => undefined);

    await Promise.resolve();
    await Promise.resolve();
    jest.advanceTimersByTime(1000);
    await Promise.resolve();

    expect(subscribe).toHaveBeenCalledTimes(2);
    expect(consoleError).not.toHaveBeenCalled();
    unsubscribe();
  });
});
