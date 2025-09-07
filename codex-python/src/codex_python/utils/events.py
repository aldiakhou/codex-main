import asyncio
from typing import AsyncIterator, Callable, Dict, List, Optional


class EventBus:
    """Simple in-proc async event bus with type filtering."""

    def __init__(self) -> None:
        self._subscribers: List[asyncio.Queue] = []

    async def publish(self, event_type: str, **fields) -> None:
        envelope = {"type": event_type, **fields}
        # copy queues to avoid mutation mid-iteration
        for q in list(self._subscribers):
            # Non-blocking: drop if queue is too full
            if q.qsize() < 1000:
                await q.put(envelope)

    async def subscribe(self, types: Optional[List[str]] = None) -> AsyncIterator[Dict]:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(q)

        try:
            while True:
                ev = await q.get()
                if types is None or ev.get("type") in types:
                    yield ev
        finally:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

