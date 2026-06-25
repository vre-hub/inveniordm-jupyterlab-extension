import asyncio
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    topic: str
    data: dict[str, Any] | None = None


class EventBus:
    def __init__(self):
        self._queues_by_subscription: dict[
            tuple[str, str],
            set[asyncio.Queue[DomainEvent]],
        ] = defaultdict(set)

    def subscribe(
        self,
        user_id: str,
        topics: Iterable[str],
    ) -> asyncio.Queue[DomainEvent]:
        topics = set(topics)
        if not topics:
            raise ValueError("At least one topic is required")

        queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        for topic in topics:
            self._queues_by_subscription[(user_id, topic)].add(queue)
        return queue

    def unsubscribe(
        self,
        user_id: str,
        topics: Iterable[str],
        queue: asyncio.Queue[DomainEvent],
    ) -> None:
        for topic in topics:
            self._queues_by_subscription[(user_id, topic)].discard(queue)

    def publish(
        self,
        user_id: str,
        topic: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        event = DomainEvent(topic=topic, data=data)
        for queue in list(self._queues_by_subscription[(user_id, topic)]):
            queue.put_nowait(event)
