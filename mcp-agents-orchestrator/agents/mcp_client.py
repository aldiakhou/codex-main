"""
MCP client helpers using the official MCP Python SDK.

Two modes provided:
- Atomic (one-shot) operations for simple list/call usage.
- Persistent session manager for long-lived stdio connections with reuse.

Enhancements:
- Load server config from mcp.config.json with environment substitution.
- Robust parsing of tool results (structuredContent or text fallback).
- Timeouts and one-shot auto-reconnect on failures.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from .policy import is_stdio_command_allowed, is_http_url_allowed


class MCPClientManager:
    """Singleton manager for shared persistent MCP stdio clients."""
    _clients: Dict[str, 'PersistentMCPClient'] = {}

    @staticmethod
    def _key_from_config(server_config: Dict[str, Any]) -> str:
        args = server_config.get('args') or []
        env = server_config.get('env') or {}
        env_key = ",".join(sorted(f"{k}={v}" for k, v in env.items()))
        return f"{server_config['command']}::{ ' '.join(args) }::{env_key}"

    @classmethod
    async def get_or_create(cls, server_config: Dict[str, Any]) -> Optional['PersistentMCPClient']:
        """Get or establish a persistent client for this server config."""
        cmd = str(server_config.get('command') or '')
        if not is_stdio_command_allowed(cmd):
            return None
        key = cls._key_from_config(server_config)
        client = cls._clients.get(key)
        if client and client.is_connected:
            return client
        # Create and connect
        client = PersistentMCPClient(server_config)
        ok = await client.connect()
        if not ok:
            return None
        cls._clients[key] = client
        return client

    @classmethod
    async def cleanup_all(cls):
        """Disconnect all persistent clients."""
        for key, client in list(cls._clients.items()):
            try:
                await client.disconnect()
            finally:
                pass
        cls._clients.clear()

    @classmethod
    def count(cls) -> int:
        return len(cls._clients)


# ---------------------------
# Config helpers
# ---------------------------
def load_mcp_server_config(name: str = "ai_tools") -> Dict[str, Any]:
    """Load MCP server config from mcp.config.json if present.

    Supports ${PYTHON_EXECUTABLE} substitution. Falls back to running the
    built-in AI tools server via current Python if file is missing or invalid.
    """
    try:
        # repo root is two levels up from this file (mindrobot/agents)
        root = Path(__file__).resolve().parents[2]
        cfg_path = root / "mcp.config.json"
        if cfg_path.exists():
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            servers = data.get("mcpServers", {})
            server = servers.get(name) or next(iter(servers.values()), None)
            if isinstance(server, dict):
                command = server.get("command") or sys.executable
                if isinstance(command, str) and "${PYTHON_EXECUTABLE}" in command:
                    command = command.replace("${PYTHON_EXECUTABLE}", sys.executable)
                args = server.get("args") or ["-m", "mindrobot.mcp_servers.ai_tools_server"]
                # Start from parent environment to preserve credentials like OPENAI_API_KEY
                env = dict(os.environ)
                # Overlay any explicit env from config
                env.update(dict(server.get("env") or {}))
                # Ensure PYTHONPATH includes repo root so -m imports work from any CWD
                existing_pp = os.environ.get("PYTHONPATH", "")
                sep = os.pathsep
                # Prepend repo root if not already present
                if str(root) not in existing_pp.split(sep):
                    env["PYTHONPATH"] = f"{str(root)}{sep}{existing_pp}" if existing_pp else str(root)
                else:
                    env["PYTHONPATH"] = existing_pp
                # Route logs to stderr and use unbuffered I/O for stdio reliability
                env.setdefault("MCP_STDIO_MODE", "true")
                env.setdefault("PYTHONUNBUFFERED", "1")
                # Force UTF-8 to prevent encoding issues on Windows
                env.setdefault("PYTHONIOENCODING", "utf-8")
                return {"command": command, "args": args, "env": env}
    except Exception:
        # fall through to default
        pass
    # Fallback config with safe environment for stdio MCP
    root = Path(__file__).resolve().parents[2]
    # Start from parent environment to preserve credentials like OPENAI_API_KEY
    env: Dict[str, str] = dict(os.environ)
    # Route logs to stderr in stdio mode
    env["MCP_STDIO_MODE"] = "true"
    # Ensure module imports work regardless of CWD
    existing_pp = os.environ.get("PYTHONPATH", "")
    sep = os.pathsep
    if str(root) not in existing_pp.split(sep):
        env["PYTHONPATH"] = f"{str(root)}{sep}{existing_pp}" if existing_pp else str(root)
    else:
        env["PYTHONPATH"] = existing_pp
    # Unbuffered I/O for reliability
    env["PYTHONUNBUFFERED"] = "1"
    # Force UTF-8 to prevent encoding issues on Windows
    env["PYTHONIOENCODING"] = "utf-8"
    return {"command": sys.executable, "args": ["-m", "mindrobot.mcp_servers.ai_tools_server"], "env": env}


def load_mcp_http_url() -> Optional[str]:
    """Load optional HTTP transport URL from env or config for probing.

    Order:
    - Env var MCP_HTTP_URL
    - mcp.config.json: mcpServers[ai_tools].httpUrl
    """
    # Environment has priority
    url = os.environ.get("MCP_HTTP_URL")
    if url:
        return url
    try:
        root = Path(__file__).resolve().parents[2]
        cfg_path = root / "mcp.config.json"
        if cfg_path.exists():
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            servers = data.get("mcpServers", {})
            server = servers.get("ai_tools") or next(iter(servers.values()), None)
            if isinstance(server, dict):
                http_url = server.get("httpUrl")
                if isinstance(http_url, str) and http_url:
                    return http_url
    except Exception:
        pass
    return None


class PocketFlowMCPClient:
    """Atomic one-shot MCP client using the SDK with self-contained operations."""

    def __init__(self, server_config: Dict[str, Any]):
        self.server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config["args"],
            env=server_config.get("env"),
        )

    async def list_tools_atomic(self) -> List[Dict[str, Any]]:
        """Get available tools in a single atomic operation"""
        try:
            # Handle entire MCP lifecycle within single async context
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    tools_response = await session.list_tools()
                    # Convert MCP tool objects to dicts for compatibility
                    tools = []
                    for tool in tools_response.tools:
                        tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        })
                    return tools
                    
        except Exception as e:
            # Avoid noisy stdout; rely on caller logs
            return []

    async def list_resources_atomic(self) -> List[Dict[str, Any]]:
        try:
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    res = await session.list_resources()
                    return [
                        {
                            "uri": r.uri,
                            "name": getattr(r, "name", None),
                            "mimeType": getattr(r, "mimeType", None),
                        }
                        for r in res.resources
                    ]
        except Exception:
            return []

    async def list_prompts_atomic(self) -> List[Dict[str, Any]]:
        try:
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    res = await session.list_prompts()
                    return [
                        {
                            "name": p.name,
                            "description": getattr(p, "description", None),
                            "arguments": getattr(p, "arguments", None),
                        }
                        for p in res.prompts
                    ]
        except Exception:
            return []

    async def call_tool_atomic(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool in a single atomic operation"""
        try:
            # Handle entire MCP lifecycle within single async context
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(tool_name, arguments)

                    # Prefer structured content when available
                    payload = getattr(result, "structuredContent", None)
                    if payload is None and getattr(result, "content", None):
                        content = result.content[0]
                        if hasattr(content, "text"):
                            payload = content.text
                        else:
                            payload = str(content)
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except Exception:
                            pass
                    # Derive a more accurate success flag from payload when possible
                    success = True
                    try:
                        if isinstance(payload, dict):
                            if payload.get("success") is False:
                                success = False
                            elif isinstance(payload.get("result"), dict) and payload["result"].get("success") is False:
                                success = False
                        if isinstance(payload, str) and payload.lower().startswith("unknown tool:"):
                            success = False
                    except Exception:
                        pass
                    return {"result": payload if payload is not None else "No content returned", "success": success}

        except Exception as e:
            return {"error": str(e), "success": False}

    # HTTP transport (streamable) one-shot helpers
    @staticmethod
    async def list_tools_http(http_url: str) -> List[Dict[str, Any]]:
        try:
            async with streamablehttp_client(http_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_response = await session.list_tools()
                    return [
                        {
                            "name": t.name,
                            "description": getattr(t, "description", None),
                            "inputSchema": getattr(t, "inputSchema", None),
                        }
                        for t in tools_response.tools
                    ]
        except Exception:
            return []

    @staticmethod
    async def call_tool_http(http_url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not is_http_url_allowed(http_url):
                return {"success": False, "error": "HTTP MCP URL not allowed by policy"}
            async with streamablehttp_client(http_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    payload = getattr(result, "structuredContent", None)
                    if payload is None and getattr(result, "content", None):
                        # Merge text items
                        texts = []
                        for item in result.content:
                            if hasattr(item, "text"):
                                texts.append(item.text)
                        payload = "\n".join(texts) if texts else None
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except Exception:
                            pass
                    # Derive a more accurate success flag from payload when possible
                    success = True
                    try:
                        if isinstance(payload, dict):
                            if payload.get("success") is False:
                                success = False
                            elif isinstance(payload.get("result"), dict) and payload["result"].get("success") is False:
                                success = False
                        if isinstance(payload, str) and payload.lower().startswith("unknown tool:"):
                            success = False
                    except Exception:
                        pass
                    return {"result": payload if payload is not None else "No content returned", "success": success}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def list_resources_http(http_url: str) -> List[Dict[str, Any]]:
        try:
            if not is_http_url_allowed(http_url):
                return []
            async with streamablehttp_client(http_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    res = await session.list_resources()
                    return [
                        {"uri": r.uri, "name": getattr(r, "name", None), "mimeType": getattr(r, "mimeType", None)}
                        for r in res.resources
                    ]
        except Exception:
            return []

    @staticmethod
    async def list_prompts_http(http_url: str) -> List[Dict[str, Any]]:
        try:
            if not is_http_url_allowed(http_url):
                return []
            async with streamablehttp_client(http_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    res = await session.list_prompts()
                    return [
                        {"name": p.name, "description": getattr(p, "description", None), "arguments": getattr(p, "arguments", None)}
                        for p in res.prompts
                    ]
        except Exception:
            return []


class PersistentMCPClient:
    """Persistent stdio MCP client with reusable ClientSession.

    Notes:
    - Uses underlying async context managers via __aenter__/__aexit__ to control lifespan.
    - Serialized access with an asyncio.Lock to prevent interleaved requests on one session.
    """

    def __init__(self, server_config: Dict[str, Any]):
        self.server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env"),
        )
        self._client_cm = None
        self._session_cm = None
        self._session: Optional[ClientSession] = None
        self._lock = asyncio.Lock()
        self.is_connected = False
        self._timeout = float(server_config.get("timeout", 20.0))

    async def connect(self) -> bool:
        if self.is_connected:
            return True
        try:
            self._client_cm = stdio_client(self.server_params)
            read_stream, write_stream = await self._client_cm.__aenter__()
            self._session_cm = ClientSession(read_stream, write_stream)
            self._session = await self._session_cm.__aenter__()
            await self._session.initialize()
            self.is_connected = True
            return True
        except Exception as e:
            await self._safe_close()
            return False

    async def disconnect(self):
        await self._safe_close()

    async def _safe_close(self):
        try:
            if self._session_cm is not None:
                await self._session_cm.__aexit__(None, None, None)
        except Exception:
            pass
        try:
            if self._client_cm is not None:
                await self._client_cm.__aexit__(None, None, None)
        except Exception:
            pass
        self._session = None
        self._session_cm = None
        self._client_cm = None
        self.is_connected = False

    async def ensure(self) -> bool:
        if not self.is_connected:
            return await self.connect()
        return True

    async def list_tools(self) -> List[Dict[str, Any]]:
        if not await self.ensure():
            return []
        async with self._lock:
            try:
                tools_response = await asyncio.wait_for(self._session.list_tools(), timeout=self._timeout)
                return [
                    {
                        "name": t.name,
                        "description": getattr(t, "description", None),
                        "inputSchema": getattr(t, "inputSchema", None),
                    }
                    for t in tools_response.tools
                ]
            except Exception as e:
                return []

    async def list_resources(self) -> List[Dict[str, Any]]:
        if not await self.ensure():
            return []
        async with self._lock:
            try:
                res = await asyncio.wait_for(self._session.list_resources(), timeout=self._timeout)
                return [
                    {
                        "uri": r.uri,
                        "name": getattr(r, "name", None),
                        "mimeType": getattr(r, "mimeType", None),
                    }
                    for r in res.resources
                ]
            except Exception:
                return []

    async def list_prompts(self) -> List[Dict[str, Any]]:
        if not await self.ensure():
            return []
        async with self._lock:
            try:
                res = await asyncio.wait_for(self._session.list_prompts(), timeout=self._timeout)
                return [
                    {
                        "name": p.name,
                        "description": getattr(p, "description", None),
                        "arguments": getattr(p, "arguments", None),
                    }
                    for p in res.prompts
                ]
            except Exception:
                return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not await self.ensure():
            return {"success": False, "error": "not_connected"}
        async with self._lock:
            try:
                result = await asyncio.wait_for(self._session.call_tool(tool_name, arguments), timeout=self._timeout)
            except Exception as e:
                # Try a one-time reconnect then retry the call
                try:
                    await self._safe_close()
                    await self.connect()
                    result = await asyncio.wait_for(self._session.call_tool(tool_name, arguments), timeout=self._timeout)
                except Exception as e2:
                    return {"success": False, "error": f"{e}; retry: {e2}"}

            # Parse result (structuredContent preferred)
            payload = getattr(result, "structuredContent", None)
            if payload is None and getattr(result, "content", None):
                content = result.content[0]
                if hasattr(content, "text"):
                    payload = content.text
                else:
                    payload = str(content)
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    pass
            return {"result": payload if payload is not None else "No content returned", "success": True}
