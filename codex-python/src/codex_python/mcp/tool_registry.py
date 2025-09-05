"""
Tool Registry for managing and validating MCP tools
"""

import asyncio
import re
import structlog
from typing import Dict, List, Set, Optional, Any, Pattern
from dataclasses import dataclass, field
from enum import Enum

from mcp import ClientSession
from mcp.types import Tool
import hashlib

from ..core.config import Config


logger = structlog.get_logger(__name__)


class ToolPermission(Enum):
    """Tool permission levels"""
    ALLOW = "allow"
    BLOCK = "block"
    SANDBOX = "sandbox"


@dataclass
class ToolInfo:
    """Information about a registered tool"""
    name: str
    description: str
    server_name: str
    input_schema: Dict[str, Any]
    permission: ToolPermission = ToolPermission.ALLOW
    category: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    usage_count: int = 0
    last_used: Optional[float] = None
    estimated_runtime: Optional[float] = None
    
    def should_sandbox(self) -> bool:
        """Check if tool should be sandboxed"""
        return (
            self.permission == ToolPermission.SANDBOX or
            "file" in self.tags or
            "system" in self.tags or
            "network" in self.tags or
            self._is_potentially_dangerous()
        )
    
    def _is_potentially_dangerous(self) -> bool:
        """Check if tool is potentially dangerous"""
        dangerous_patterns = [
            r"(?i)(delete|remove|rm)",
            r"(?i)(exec|eval|shell)",
            r"(?i)(write|create).*file",
            r"(?i)(download|upload)",
            r"(?i)(system|os\.)",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, self.description):
                return True
        
        return False


MCP_TOOL_NAME_DELIMITER = "__"
MAX_TOOL_NAME_LENGTH = 64


def _qualify_name(server: str, tool: str) -> str:
    name = f"{server}{MCP_TOOL_NAME_DELIMITER}{tool}"
    if len(name) <= MAX_TOOL_NAME_LENGTH:
        return name
    h = hashlib.sha1(name.encode()).hexdigest()
    prefix = MAX_TOOL_NAME_LENGTH - len(h)
    return f"{name[:prefix]}{h}"


class ToolRegistry:
    """Registry for managing MCP tools with security controls"""
    
    def __init__(self, config: Config):
        self.config = config
        # Qualified tool name -> ToolInfo
        self.tools: Dict[str, ToolInfo] = {}
        # Server -> set of qualified tool names
        self.server_tools: Dict[str, Set[str]] = {}
        # Raw tool name index to support backwards compat unqualified lookup
        self._unqualified_index: Dict[str, Set[str]] = {}
        # Reverse lookup: id(ToolInfo) -> qualified name
        self._reverse_ids: Dict[int, str] = {}
        self._initialized = False
        
        # Precompile regex patterns for efficiency
        self._tool_name_patterns: Dict[str, Pattern] = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for tool matching"""
        # Add tool name patterns from configuration
        for pattern in self.config.allowed_tools:
            if pattern.strip():
                try:
                    compiled = re.compile(pattern)
                    self._tool_name_patterns[f"allow_{pattern}"] = compiled
                except re.error as e:
                    logger.warning("Invalid allow pattern", pattern=pattern, error=str(e))
        
        for pattern in self.config.blocked_tools:
            if pattern.strip():
                try:
                    compiled = re.compile(pattern)
                    self._tool_name_patterns[f"block_{pattern}"] = compiled
                except re.error as e:
                    logger.warning("Invalid block pattern", pattern=pattern, error=str(e))
    
    async def initialize(self, sessions: Dict[str, ClientSession]) -> None:
        """Initialize the tool registry with available tools"""
        logger.info("Initializing tool registry")
        
        for server_name, session in sessions.items():
            try:
                await self._load_server_tools(server_name, session)
            except Exception as e:
                logger.error("Failed to load tools from server", server=server_name, error=str(e))
                continue
        
        self._initialized = True
        logger.info("Tool registry initialized", tools=len(self.tools))
    
    async def _load_server_tools(self, server_name: str, session: ClientSession) -> None:
        """Load tools from a specific server"""
        try:
            result = await session.list_tools()
            server_tools = set()

            for tool in result.tools:
                tool_info = self._create_tool_info(tool, server_name)
                qualified = _qualify_name(server_name, tool.name)
                self.tools[qualified] = tool_info
                self._reverse_ids[id(tool_info)] = qualified
                server_tools.add(qualified)
                # index unqualified for fallback resolution
                self._unqualified_index.setdefault(tool.name, set()).add(qualified)

                logger.debug("Tool registered", tool=tool.name, server=server_name)

            self.server_tools[server_name] = server_tools
            logger.info("Server tools loaded", server=server_name, count=len(server_tools))
            
        except Exception as e:
            logger.error("Failed to load server tools", server=server_name, error=str(e))
            raise
    
    def _create_tool_info(self, tool: Tool, server_name: str) -> ToolInfo:
        """Create ToolInfo from MCP Tool"""
        # Determine permission based on configuration
        permission = self._determine_tool_permission(tool.name)
        
        # Extract category and tags from description
        category, tags = self._extract_metadata(tool.description)
        
        return ToolInfo(
            name=tool.name,
            description=tool.description,
            server_name=server_name,
            input_schema=tool.inputSchema,
            permission=permission,
            category=category,
            tags=tags
        )
    
    def _determine_tool_permission(self, tool_name: str) -> ToolPermission:
        """Determine tool permission based on configuration"""
        # Check blocked patterns first
        for pattern_name, pattern in self._tool_name_patterns.items():
            if pattern_name.startswith("block_") and pattern.search(tool_name):
                logger.info("Tool blocked by pattern", tool=tool_name, pattern=pattern_name)
                return ToolPermission.BLOCK
        
        # Check allowed patterns
        has_allow_pattern = any(
            pattern_name.startswith("allow_") for pattern_name in self._tool_name_patterns.keys()
        )
        
        if has_allow_pattern:
            # Only allow if matches an allow pattern
            for pattern_name, pattern in self._tool_name_patterns.items():
                if pattern_name.startswith("allow_") and pattern.search(tool_name):
                    return ToolPermission.ALLOW
            
            # No allow pattern matched
            return ToolPermission.BLOCK
        else:
            # No allow patterns configured, allow by default
            return ToolPermission.ALLOW
    
    def _extract_metadata(self, description: str) -> tuple[Optional[str], Set[str]]:
        """Extract category and tags from tool description"""
        category = None
        tags = set()
        
        # Look for category hints in description
        category_patterns = [
            r"(?i)category:\s*(\w+)",
            r"(?i)type:\s*(\w+)",
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, description)
            if match:
                category = match.group(1).lower()
                break
        
        # Look for tag hints
        tag_patterns = [
            r"(?i)tags?:\s*([^.\n]+)",
        ]
        
        for pattern in tag_patterns:
            match = re.search(pattern, description)
            if match:
                tag_text = match.group(1)
                # Split by commas and clean up
                for tag in tag_text.split(","):
                    tag = tag.strip().lower()
                    if tag:
                        tags.add(tag)
        
        # Auto-categorize based on description keywords
        if not category:
            desc_lower = description.lower()
            if any(keyword in desc_lower for keyword in ["file", "directory", "path"]):
                category = "file"
                tags.add("file")
            elif any(keyword in desc_lower for keyword in ["http", "url", "web", "api"]):
                category = "network"
                tags.add("network")
            elif any(keyword in desc_lower for keyword in ["execute", "run", "command", "shell"]):
                category = "system"
                tags.add("system")
            elif any(keyword in desc_lower for keyword in ["database", "sql", "query"]):
                category = "database"
                tags.add("database")
            elif any(keyword in desc_lower for keyword in ["calculate", "math", "compute"]):
                category = "utility"
                tags.add("utility")
        
        return category, tags
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed to be used"""
        qname = self.resolve_tool_name(tool_name)
        if qname is None or qname not in self.tools:
            return False
        tool_info = self.tools[qname]
        return tool_info.permission != ToolPermission.BLOCK
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """Get information about a specific tool"""
        qname = self.resolve_tool_name(tool_name)
        return self.tools.get(qname) if qname else None
    
    def list_tools(
        self, 
        server_name: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        permission: Optional[ToolPermission] = None
    ) -> List[ToolInfo]:
        """List tools with optional filtering"""
        tools = list(self.tools.values())
        
        # Filter by server
        if server_name:
            tools = [t for t in tools if t.server_name == server_name]
        
        # Filter by category
        if category:
            tools = [t for t in tools if t.category == category]
        
        # Filter by tags
        if tags:
            tools = [t for t in tools if tags.intersection(t.tags)]
        
        # Filter by permission
        if permission:
            tools = [t for t in tools if t.permission == permission]
        
        return tools
    
    def get_tools_by_server(self) -> Dict[str, List[ToolInfo]]:
        """Get tools grouped by server"""
        server_tools: Dict[str, List[ToolInfo]] = {}
        
        for tool_info in self.tools.values():
            if tool_info.server_name not in server_tools:
                server_tools[tool_info.server_name] = []
            server_tools[tool_info.server_name].append(tool_info)
        
        return server_tools
    
    def get_tools_by_category(self) -> Dict[str, List[ToolInfo]]:
        """Get tools grouped by category"""
        category_tools: Dict[str, List[ToolInfo]] = {}
        
        for tool_info in self.tools.values():
            category = tool_info.category or "uncategorized"
            if category not in category_tools:
                category_tools[category] = []
            category_tools[category].append(tool_info)
        
        return category_tools
    
    def record_tool_usage(self, tool_name: str, execution_time: Optional[float] = None) -> None:
        """Record tool usage for analytics"""
        if tool_name not in self.tools:
            return
        
        tool_info = self.tools[tool_name]
        tool_info.usage_count += 1
        tool_info.last_used = asyncio.get_event_loop().time()
        
        if execution_time:
            # Update estimated runtime (simple moving average)
            if tool_info.estimated_runtime is None:
                tool_info.estimated_runtime = execution_time
            else:
                alpha = 0.3  # Smoothing factor
                tool_info.estimated_runtime = (
                    alpha * execution_time + (1 - alpha) * tool_info.estimated_runtime
                )
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for tools"""
        if not self.tools:
            return {}
        
        total_usage = sum(t.usage_count for t in self.tools.values())
        tools_by_permission = {
            permission.value: [t for t in self.tools.values() if t.permission == permission]
            for permission in ToolPermission
        }
        
        return {
            "total_tools": len(self.tools),
            "total_usage": total_usage,
            "allowed_tools": len(tools_by_permission[ToolPermission.ALLOW.value]),
            "blocked_tools": len(tools_by_permission[ToolPermission.BLOCK.value]),
            "sandboxed_tools": len(tools_by_permission[ToolPermission.SANDBOX.value]),
            "most_used_tools": sorted(
                self.tools.values(),
                key=lambda t: t.usage_count,
                reverse=True
            )[:10],
            "categories": {
                category: len(tools)
                for category, tools in self.get_tools_by_category().items()
            }
        }
    
    def validate_tool_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments against schema"""
        if tool_name not in self.tools:
            return False
        
        tool_info = self.tools[tool_name]
        schema = tool_info.input_schema
        
        # Basic validation - in a real implementation, you'd use jsonschema
        if not isinstance(arguments, dict):
            return False
        
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in arguments:
                return False
        
        # Check field types
        properties = schema.get("properties", {})
        for field, value in arguments.items():
            if field in properties:
                field_schema = properties[field]
                expected_type = field_schema.get("type")
                
                if expected_type and not self._validate_type(value, expected_type):
                    return False
        
        return True
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type against expected type"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, assume valid
    
    def refresh_tools(self, sessions: Dict[str, ClientSession]) -> None:
        """Refresh tool registry with updated sessions"""
        logger.info("Refreshing tool registry")

        # Clear existing tools
        self.tools.clear()
        self.server_tools.clear()
        self._unqualified_index.clear()
        self._reverse_ids.clear()

        # Reload tools
        asyncio.create_task(self.initialize(sessions))

    def resolve_tool_name(self, name: str) -> Optional[str]:
        """Resolve possibly-unqualified name to a qualified one.

        - If already qualified and known, return as-is.
        - If unqualified and unique across servers, return that qualified name.
        - If ambiguous or unknown, return None.
        """
        if name in self.tools:
            return name
        matches = self._unqualified_index.get(name, set())
        if not matches:
            return None
        if len(matches) == 1:
            return next(iter(matches))
        # ambiguous
        return None

    def qualified_name_for(self, info: ToolInfo) -> Optional[str]:
        return self._reverse_ids.get(id(info))

    def server_and_tool_from_qualified(self, name: str) -> Optional[tuple[str, str]]:
        """Return (server, raw_tool_name) if name resolves and matches pattern."""
        q = self.resolve_tool_name(name)
        if not q:
            return None
        info = self.tools[q]
        # We don't store raw tool name separately; reconstruct from qualified if possible
        # or return qualified as tool name (server may still route by session).
        if MCP_TOOL_NAME_DELIMITER in q:
            server, _rest = q.split(MCP_TOOL_NAME_DELIMITER, 1)
            return server, info.name
        return info.server_name, info.name
