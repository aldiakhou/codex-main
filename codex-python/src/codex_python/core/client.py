"""
Core client implementation for Codex Python
"""

import asyncio
import json
import structlog
from typing import Dict, List, Optional, Any, Union, AsyncIterator, Callable
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import (
    CallToolRequest, 
    CallToolResult,
    ListToolsRequest,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)

from .config import Config, ServerConfig
from ..mcp.connection_manager import MCPConnectionManager
from ..mcp.tool_registry import ToolRegistry


logger = structlog.get_logger(__name__)


class CodexClient:
    """Main client for interacting with MCP servers"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.connection_manager = MCPConnectionManager(self.config)
        self.tool_registry = ToolRegistry(self.config)
        self._sessions: Dict[str, ClientSession] = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the client and connect to all configured servers"""
        if self._initialized:
            return
            
        logger.info("Initializing Codex client", servers=list(self.config.servers.keys()))
        # Use connection manager to start and monitor sessions
        await self.connection_manager.start()
        healthy = await self.connection_manager.get_healthy_sessions()
        self._sessions = healthy

        # Initialize tool registry from connection manager
        await self.tool_registry.initialize(self._sessions)
        self._initialized = True
        
        logger.info("Codex client initialized successfully")

    # Async context manager helpers for tests/CLI ergonomics
    async def __aenter__(self) -> "CodexClient":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        """Close all sessions and stop the connection manager."""
        try:
            for name, session in list(self._sessions.items()):
                try:
                    await session.close()
                except Exception:
                    pass
                self._sessions.pop(name, None)
        except Exception:
            pass
        try:
            await self.connection_manager.stop()
        except Exception:
            pass
        self._initialized = False
    
    async def _connect_to_server(self, server_name: str, server_config: ServerConfig) -> None:
        """Connect to a specific MCP server"""
        logger.info("Connecting to server", server=server_name, transport=server_config.transport)
        
        if server_config.transport == "stdio":
            await self._connect_stdio(server_name, server_config)
        elif server_config.transport == "streamable_http":
            await self._connect_http(server_name, server_config)
        else:
            raise ValueError(f"Unsupported transport: {server_config.transport}")
    
    async def _connect_stdio(self, server_name: str, server_config: ServerConfig) -> None:
        """Connect using stdio transport"""
        server_params = StdioServerParameters(
            command=server_config.command,
            args=server_config.args,
            env=server_config.env
        )
        
        async with stdio_client(server_params) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            self._sessions[server_name] = session
            
            # List available tools
            tools_result = await session.list_tools()
            logger.info("Server tools loaded", server=server_name, count=len(tools_result.tools))
    
    async def _connect_http(self, server_name: str, server_config: ServerConfig) -> None:
        """Connect using HTTP transport"""
        if not server_config.url:
            raise ValueError(f"URL required for HTTP transport: {server_name}")
        
        async with streamablehttp_client(server_config.url) as (read_stream, write_stream, _):
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            self._sessions[server_name] = session
            
            # List available tools
            tools_result = await session.list_tools()
            logger.info("Server tools loaded", server=server_name, count=len(tools_result.tools))
    
    async def list_tools(self, server_name: Optional[str] = None) -> List[Tool]:
        """List available tools from server(s)"""
        if not self._initialized:
            await self.initialize()
        
        if server_name:
            if server_name not in self._sessions:
                raise ValueError(f"Server not connected: {server_name}")
            
            result = await self._sessions[server_name].list_tools()
            return result.tools
        else:
            # Get tools from all servers
            all_tools = []
            for name, session in self._sessions.items():
                try:
                    result = await session.list_tools()
                    all_tools.extend(result.tools)
                except Exception as e:
                    logger.error("Failed to list tools from server", server=name, error=str(e))
                    continue
            
            return all_tools
    
    async def call_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> CallToolResult:
        """Call a tool on a specific server"""
        if not self._initialized:
            await self.initialize()

        # Resolve qualified or unqualified tool name via registry
        qname = self.tool_registry.resolve_tool_name(tool_name)
        if qname is None and server_name is None:
            raise ValueError(f"Tool not found or ambiguous: {tool_name}")

        if server_name:
            target_server = server_name
        else:
            pair = self.tool_registry.server_and_tool_from_qualified(qname or tool_name)
            if not pair:
                raise ValueError(f"Unable to resolve tool '{tool_name}'. Specify --server.")
            target_server, _ = pair

        if target_server not in self._sessions:
            raise ValueError(f"Server not connected: {target_server}")

        # Check if tool is allowed
        if not self.tool_registry.is_tool_allowed(tool_name):
            raise ValueError(f"Tool not allowed: {tool_name}")
        
        logger.info("Calling tool", tool=tool_name, server=target_server)
        
        try:
            # Use raw tool name expected by server (unqualified)
            server_tool = tool_name
            if not server_name:
                pair = self.tool_registry.server_and_tool_from_qualified(qname or tool_name)
                if pair:
                    _server, server_tool = pair
            result = await self._sessions[target_server].call_tool(server_tool, arguments)
            logger.info("Tool call completed", tool=tool_name, server=target_server)
            return result
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, server=target_server, error=str(e))
            raise
    
    async def stream_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> AsyncIterator[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Stream tool call results"""
        if not self._initialized:
            await self.initialize()
        
        result = await self.call_tool(tool_name, arguments, server_name)
        
        for content in result.content:
            yield content
    
    async def get_server_info(self, server_name: str) -> Dict[str, Any]:
        """Get information about a connected server"""
        if server_name not in self._sessions:
            raise ValueError(f"Server not connected: {server_name}")
        
        session = self._sessions[server_name]
        
        try:
            # Try to get server capabilities
            tools_result = await session.list_tools()
            return {
                "name": server_name,
                "connected": True,
                "tool_count": len(tools_result.tools),
                "tools": [tool.name for tool in tools_result.tools]
            }
        except Exception as e:
            return {
                "name": server_name,
                "connected": False,
                "error": str(e)
            }
    
    async def get_all_servers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all connected servers"""
        info = {}
        for server_name in self._sessions.keys():
            info[server_name] = await self.get_server_info(server_name)
        return info
    
    async def _close_manager_only(self) -> None:
        """Close connection manager (legacy helper)."""
        logger.info("Closing Codex client")
        try:
            await self.connection_manager.stop()
        except Exception as e:
            logger.error("Error stopping connection manager", error=str(e))
        self._sessions.clear()
        self._initialized = False
        
        logger.info("Codex client closed")

    @asynccontextmanager
    async def session(self) -> AsyncIterator["CodexClient"]:
        """Context manager for client session"""
        try:
            if not self._initialized:
                await self.initialize()
            yield self
        finally:
            await self._close_manager_only()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all connections"""
        if not self._initialized:
            return {"status": "not_initialized", "servers": {}}
        
        servers_status = {}
        healthy_count = 0
        
        for server_name, session in self._sessions.items():
            try:
                # Try to list tools as a health check
                await session.list_tools()
                servers_status[server_name] = {"status": "healthy"}
                healthy_count += 1
            except Exception as e:
                servers_status[server_name] = {"status": "unhealthy", "error": str(e)}
        
        overall_status = "healthy" if healthy_count == len(self._sessions) else "degraded"
        if healthy_count == 0:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "healthy_servers": healthy_count,
            "total_servers": len(self._sessions),
            "servers": servers_status
        }

    # --- Notifications (best-effort) ---
    async def progress_events(
        self,
        kinds: Optional[List[str]] = None,
        server_name: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Yield notifications/progress events if the client SDK exposes a notification hook.

        This is best-effort; if the underlying ClientSession does not support notification
        subscriptions, this async generator will yield nothing.
        """
        if not self._initialized:
            await self.initialize()

        sessions: Dict[str, ClientSession] = (
            {server_name: self._sessions[server_name]}
            if server_name and server_name in self._sessions
            else self._sessions
        )

        queue: asyncio.Queue = asyncio.Queue()

        # Try to register a notification handler for each session.
        unregisters: List[Callable[[], None]] = []

        def _make_handler(server: str):
            def _handler(*args, **kwargs):
                # Try to extract method/params heuristically
                method = kwargs.get("method") or kwargs.get("name") or None
                params = kwargs.get("params") or (args[0] if args else None)
                payload = params if isinstance(params, dict) else {"value": params}
                payload = payload or {}
                # Expect { kind, ... }
                if kinds and payload.get("kind") not in kinds:
                    return
                try:
                    queue.put_nowait({"server": server, **payload})
                except Exception:
                    pass

            return _handler

        for name, sess in sessions.items():
            handler = _make_handler(name)
            # Attempt multiple common SDK patterns
            unregister = None
            try:
                if hasattr(sess, "on_notification"):
                    # Newer SDKs may support method + callback
                    sess.on_notification("notifications/progress", handler)  # type: ignore[arg-type]
                    unregister = lambda s=sess: None
                elif hasattr(sess, "add_notification_handler"):
                    sess.add_notification_handler("notifications/progress", handler)  # type: ignore[attr-defined]
                    unregister = lambda s=sess: None
            except Exception:
                unregister = None

            if unregister:
                unregisters.append(unregister)

        try:
            while True:
                ev = await queue.get()
                yield ev
        finally:
            for un in unregisters:
                try:
                    un()
                except Exception:
                    pass
