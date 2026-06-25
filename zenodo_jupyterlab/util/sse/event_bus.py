import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    topic: str
    data: dict[str, Any]


class EventBus:
    def __init__(self):
        self._queues_by_user: dict[
            str,
            set[asyncio.Queue[DomainEvent]],
        ] = defaultdict(set)

    def subscribe(self, user_id: str) -> asyncio.Queue[DomainEvent]:
        queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._queues_by_user[user_id].add(queue)
        return queue

    def unsubscribe(self, user_id: str, queue: asyncio.Queue[DomainEvent]) -> None:
        self._queues_by_user[user_id].discard(queue)

    def publish(self, user_id: str, topic: str, data: dict[str, Any]) -> None:
        event = DomainEvent(topic=topic, data=data)
        for queue in list(self._queues_by_user[user_id]):
            queue.put_nowait(event)
