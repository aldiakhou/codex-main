"""
MCP Connection Manager for handling multiple server connections
"""

import asyncio
import structlog
from typing import Dict, Optional, Set, List
from dataclasses import dataclass, field

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client

from ..core.config import Config, ServerConfig


logger = structlog.get_logger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a server connection"""
    server_name: str
    session: ClientSession
    config: ServerConfig
    connected_at: float
    last_activity: float
    is_healthy: bool = True
    error_count: int = 0
    retry_count: int = 0


class MCPConnectionManager:
    """Manages connections to multiple MCP servers"""
    
    def __init__(self, config: Config):
        self.config = config
        self.connections: Dict[str, ConnectionInfo] = {}
        self._connection_lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self) -> None:
        """Start the connection manager"""
        logger.info("Starting MCP connection manager")
        self._running = True
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Connect to all configured servers
        await self._connect_all_servers()
    
    async def stop(self) -> None:
        """Stop the connection manager"""
        logger.info("Stopping MCP connection manager")
        self._running = False
        
        # Stop health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        await self._close_all_connections()
    
    async def _connect_all_servers(self) -> None:
        """Connect to all configured servers"""
        async with self._connection_lock:
            for server_name, server_config in self.config.servers.items():
                try:
                    await self._connect_server(server_name, server_config)
                except Exception as e:
                    logger.error("Failed to connect to server", server=server_name, error=str(e))
                    continue
    
    async def _connect_server(self, server_name: str, server_config: ServerConfig) -> None:
        """Connect to a specific server"""
        logger.info("Connecting to server", server=server_name, transport=server_config.transport)
        
        try:
            if server_config.transport == "stdio":
                await self._connect_stdio(server_name, server_config)
            elif server_config.transport == "streamable_http":
                await self._connect_http(server_name, server_config)
            else:
                raise ValueError(f"Unsupported transport: {server_config.transport}")
            
            logger.info("Successfully connected to server", server=server_name)
            
        except Exception as e:
            logger.error("Failed to connect to server", server=server_name, error=str(e))
            raise
    
    async def _connect_stdio(self, server_name: str, server_config: ServerConfig) -> None:
        """Connect using stdio transport"""
        server_params = StdioServerParameters(
            command=server_config.command,
            args=server_config.args,
            env=server_config.env
        )
        
        read_stream, write_stream = await stdio_client(server_params).__aenter__()
        session = ClientSession(read_stream, write_stream)
        await session.initialize()
        
        connection_info = ConnectionInfo(
            server_name=server_name,
            session=session,
            config=server_config,
            connected_at=asyncio.get_event_loop().time(),
            last_activity=asyncio.get_event_loop().time()
        )
        
        self.connections[server_name] = connection_info
    
    async def _connect_http(self, server_name: str, server_config: ServerConfig) -> None:
        """Connect using HTTP transport"""
        if not server_config.url:
            raise ValueError(f"URL required for HTTP transport: {server_name}")
        
        read_stream, write_stream, _ = await streamablehttp_client(server_config.url).__aenter__()
        session = ClientSession(read_stream, write_stream)
        await session.initialize()
        
        connection_info = ConnectionInfo(
            server_name=server_name,
            session=session,
            config=server_config,
            connected_at=asyncio.get_event_loop().time(),
            last_activity=asyncio.get_event_loop().time()
        )
        
        self.connections[server_name] = connection_info
    
    async def get_session(self, server_name: str) -> ClientSession:
        """Get a session for a specific server"""
        if server_name not in self.connections:
            raise ValueError(f"Server not connected: {server_name}")
        
        connection_info = self.connections[server_name]
        connection_info.last_activity = asyncio.get_event_loop().time()
        
        return connection_info.session
    
    async def reconnect_server(self, server_name: str) -> None:
        """Reconnect to a specific server"""
        if server_name not in self.config.servers:
            raise ValueError(f"Server not configured: {server_name}")
        
        logger.info("Reconnecting to server", server=server_name)
        
        # Close existing connection
        await self._close_connection(server_name)
        
        # Reconnect
        server_config = self.config.servers[server_name]
        await self._connect_server(server_name, server_config)
    
    async def _close_connection(self, server_name: str) -> None:
        """Close connection to a specific server"""
        if server_name not in self.connections:
            return
        
        connection_info = self.connections[server_name]
        
        try:
            await connection_info.session.close()
        except Exception as e:
            logger.error("Error closing connection", server=server_name, error=str(e))
        
        del self.connections[server_name]
    
    async def _close_all_connections(self) -> None:
        """Close all connections"""
        async with self._connection_lock:
            for server_name in list(self.connections.keys()):
                await self._close_connection(server_name)
    
    async def _health_check_loop(self) -> None:
        """Health check loop for monitoring connections"""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Health check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in health check loop", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all connections"""
        async with self._connection_lock:
            for server_name, connection_info in self.connections.items():
                try:
                    # Try to list tools as a health check
                    await connection_info.session.list_tools()
                    
                    # Update connection health
                    connection_info.is_healthy = True
                    connection_info.error_count = 0
                    connection_info.last_activity = asyncio.get_event_loop().time()
                    
                except Exception as e:
                    logger.warning("Health check failed", server=server_name, error=str(e))
                    
                    connection_info.is_healthy = False
                    connection_info.error_count += 1
                    
                    # Try to reconnect if too many errors
                    if connection_info.error_count >= 3:
                        logger.info("Attempting to reconnect", server=server_name)
                        try:
                            await self.reconnect_server(server_name)
                        except Exception as reconnect_error:
                            logger.error("Reconnection failed", server=server_name, error=str(reconnect_error))
    
    async def get_connection_status(self) -> Dict[str, Dict]:
        """Get status of all connections"""
        status = {}
        
        for server_name, connection_info in self.connections.items():
            status[server_name] = {
                "connected": True,
                "healthy": connection_info.is_healthy,
                "connected_at": connection_info.connected_at,
                "last_activity": connection_info.last_activity,
                "error_count": connection_info.error_count,
                "retry_count": connection_info.retry_count,
                "transport": connection_info.config.transport
            }
        
        # Add configured but disconnected servers
        for server_name in self.config.servers:
            if server_name not in status:
                status[server_name] = {
                    "connected": False,
                    "healthy": False,
                    "error": "Not connected"
                }
        
        return status
    
    async def get_healthy_sessions(self) -> Dict[str, ClientSession]:
        """Get all healthy sessions"""
        healthy_sessions = {}
        
        for server_name, connection_info in self.connections.items():
            if connection_info.is_healthy:
                healthy_sessions[server_name] = connection_info.session
        
        return healthy_sessions
    
    async def add_server(self, server_name: str, server_config: ServerConfig) -> None:
        """Add a new server configuration and connect"""
        async with self._connection_lock:
            self.config.servers[server_name] = server_config
            await self._connect_server(server_name, server_config)
    
    async def remove_server(self, server_name: str) -> None:
        """Remove a server configuration and disconnect"""
        async with self._connection_lock:
            await self._close_connection(server_name)
            if server_name in self.config.servers:
                del self.config.servers[server_name]
    
    async def wait_for_healthy_connection(self, server_name: str, timeout: float = 30.0) -> bool:
        """Wait for a healthy connection to a specific server"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if server_name in self.connections:
                connection_info = self.connections[server_name]
                if connection_info.is_healthy:
                    return True
            
            await asyncio.sleep(0.5)
        
        return False