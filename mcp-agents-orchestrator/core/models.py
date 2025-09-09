from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AIAgentRequest(BaseModel):
    request_id: Optional[str] = None
    text: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    cwd: Optional[str] = None
    # Optional knobs mirrored from Codex
    approval_policy: Optional[str] = None
    sandbox_mode: Optional[str] = None


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class WebSearchResponse(BaseModel):
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    total_results: Optional[int] = None
    search_time: Optional[float] = None


class ResearchSection(BaseModel):
    title: str
    content: str


class ResearchResponse(BaseModel):
    research_topic: str
    executive_summary: Optional[str] = None
    sections: List[ResearchSection] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)


class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None


class MonitoringAlert(BaseModel):
    level: str
    message: str
    metric: Optional[str] = None


class LiveMonitoringResponse(BaseModel):
    monitoring_target: Optional[str] = None
    status: str = "unknown"
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[MonitoringAlert] = Field(default_factory=list)


# Compatibility aliases some code may import
MCPToolResponse = Dict[str, Any]
ErrorSeverity = str

