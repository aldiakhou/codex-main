"""
Lightweight ConnectionAgent for suggesting connections between nodes.
Provides a minimal implementation to satisfy MCP and bridge imports.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import BaseAgentInterface
from ..core.models import (
    AIAgentRequest,
    ConnectionResponse,
    ConnectionSuggestion,
)
from ..core.logging import get_logger

logger = get_logger(__name__)


class ConnectionAgent(BaseAgentInterface):
    """Simple agent that suggests connections based on label/keyword overlap."""

    def __init__(self) -> None:
        self.name = "Connection Agent"

    async def process(self, request: AIAgentRequest) -> ConnectionResponse:
        """Generate basic connection suggestions from provided graph_data.

        Expects request.context["graph_data"] with:
        - nodes: List[Dict] where each node has at least an id and label/content
        - edges: List[[source_id, target_id]] (optional)
        """
        graph: Dict[str, Any] = request.context.get("graph_data") or {}
        nodes: List[Dict[str, Any]] = graph.get("nodes", [])

        def node_id(n: Dict[str, Any], fallback: int) -> int:
            return (
                n.get("id")
                or n.get("node_id")
                or n.get("index")
                or fallback
            )

        def text(n: Dict[str, Any]) -> str:
            return str(n.get("label") or n.get("content") or "").strip()

        def tokens(s: str) -> set:
            return {w.lower() for w in s.replace("/", " ").replace("-", " ").split() if len(w) > 3}

        suggestions: List[ConnectionSuggestion] = []
        N = len(nodes)
        for i in range(N):
            ti = text(nodes[i])
            if not ti:
                continue
            tok_i = tokens(ti)
            if not tok_i:
                continue
            for j in range(i + 1, N):
                tj = text(nodes[j])
                if not tj:
                    continue
                if tok_i.intersection(tokens(tj)):
                    suggestions.append(
                        ConnectionSuggestion(
                            source_id=node_id(nodes[i], i + 1),
                            target_id=node_id(nodes[j], j + 1),
                            reason="related keywords",
                            weight=0.7,
                        )
                    )
                if len(suggestions) >= 10:
                    break
            if len(suggestions) >= 10:
                break

        if not suggestions and N >= 2:
            # Provide a single generic suggestion to ensure non-empty output
            suggestions.append(
                ConnectionSuggestion(
                    source_id=node_id(nodes[0], 1),
                    target_id=node_id(nodes[1], 2),
                    reason="baseline connectivity",
                    weight=0.5,
                )
            )

        return ConnectionResponse(suggestions=suggestions, analysis=None)

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "connection",
            "capabilities": ["suggest_connections"],
        }


def create_connection_agent() -> ConnectionAgent:
    """Factory for ConnectionAgent (compat with existing imports)."""
    return ConnectionAgent()
