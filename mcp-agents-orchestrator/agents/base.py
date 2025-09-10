from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class AgentRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Any], Any]] = {}
        self._info: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, Any] = {}

    def register(self, agent_id: str, handler: Callable[[Any], Any], info: Optional[Dict[str, Any]] = None, instance: Optional[Any] = None) -> None:
        self._handlers[agent_id] = handler
        if info:
            self._info[agent_id] = dict(info)
        if instance is not None:
            self._instances[agent_id] = instance

    def list_agents(self) -> List[str]:
        return list(self._handlers.keys())

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._info.get(agent_id)

    def get_agent(self, agent_id: str) -> Optional[Any]:
        return self._instances.get(agent_id)

    async def process_request(self, agent_id: str, request: Any) -> Any:
        handler = self._handlers.get(agent_id)
        if not handler:
            raise ValueError(f"Unknown agent: {agent_id}")
        # Handler may be async or sync
        result = handler(request)
        if hasattr(result, "__await__"):
            return await result  # type: ignore
        return result


_REGISTRY: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AgentRegistry()
    return _REGISTRY

