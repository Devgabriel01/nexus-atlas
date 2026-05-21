"""
In-process pub/sub for scan progress events.
Simple, no external dependency — suitable for single-node deployments.
For multi-node, swap the implementation for Redis pub/sub.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator
from datetime import datetime, timezone


class EventBus:
    """One topic per scan_id. Subscribers get an async queue of events."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Emit an event to all subscribers of a topic. Non-blocking."""
        event.setdefault("ts", datetime.now(timezone.utc).isoformat())
        event.setdefault("topic", topic)
        async with self._lock:
            queues = list(self._subscribers.get(topic, []))
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # drop slow consumers

    async def subscribe(self, topic: str) -> AsyncIterator[dict[str, Any]]:
        """Yield events for a topic. Closes when caller breaks out."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=128)
        async with self._lock:
            self._subscribers[topic].append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                if queue in self._subscribers.get(topic, []):
                    self._subscribers[topic].remove(queue)
                if not self._subscribers[topic]:
                    del self._subscribers[topic]


# Module-level singleton
bus = EventBus()


def get_bus() -> EventBus:
    return bus
