"""Simple in-process pub/sub event bus (Phase 0).
Not thread-safe beyond Qt GUI thread expectations.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Callable, Dict, List, Any

Handler = Callable[[Any], None]

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler):
        if handler not in self._subscribers[topic]:
            self._subscribers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: Handler):
        if handler in self._subscribers.get(topic, []):
            self._subscribers[topic].remove(handler)

    def publish(self, topic: str, payload):
        for h in list(self._subscribers.get(topic, [])):
            try:
                h(payload)
            except Exception:  # keep bus resilient
                import traceback, sys
                print("[EventBus] handler error", file=sys.stderr)
                traceback.print_exc()

GLOBAL_EVENT_BUS = EventBus()

__all__ = ["EventBus", "GLOBAL_EVENT_BUS"]
