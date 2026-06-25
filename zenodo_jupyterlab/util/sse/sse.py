import asyncio
import json
from collections.abc import Iterable

from jupyter_server.base.handlers import APIHandler
import tornado.iostream

from .event_bus import DomainEvent, EventBus


async def stream_user_events(
    handler: APIHandler,
    *,
    event_bus: EventBus,
    user_id: str,
    initial_events: Iterable[DomainEvent] = (),
    keep_alive_seconds: int = 25,
) -> None:
    """
    Stream the events for a specific user over a Server-Sent Events (SSE) connection.
    Use the jupyter server APIHandler to write events to the response stream.
    """
    queue = event_bus.subscribe(user_id)

    handler.set_header("Content-Type", "text/event-stream")
    handler.set_header("Cache-Control", "no-cache")
    handler.set_header("Connection", "keep-alive")

    try:
        try:
            for event in initial_events:
                handler.write(f"event: {event.topic}\n")
                handler.write(f"data: {json.dumps(event.data)}\n\n")
            await handler.flush()

            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=keep_alive_seconds,
                    )
                except asyncio.TimeoutError:
                    handler.write(": keep-alive\n\n")
                else:
                    handler.write(f"event: {event.topic}\n")
                    handler.write(f"data: {json.dumps(event.data)}\n\n")

                await handler.flush()
        except tornado.iostream.StreamClosedError:
            pass
    finally:
        event_bus.unsubscribe(user_id, queue)
