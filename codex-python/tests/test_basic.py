"""
Basic tests for Codex Python
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from codex_python.core.config import Config, ServerConfig, AuthConfig
from codex_python.core.client import CodexClient
from codex_python.mcp.connection_manager import MCPConnectionManager
from codex_python.mcp.tool_registry import ToolRegistry, ToolInfo, ToolPermission


class TestConfig:
    """Test configuration management"""
    
    def test_config_creation(self):
        """Test basic config creation"""
        config = Config()
        assert config.timeout == 30.0
        assert config.log_level == "INFO"
        assert config.auth.type == "none"
    
    def test_server_config(self):
        """Test server configuration"""
        server_config = ServerConfig(
            name="test",
            command="echo",
            args=["hello"]
        )
        assert server_config.name == "test"
        assert server_config.command == "echo"
        assert server_config.args == ["hello"]
    
    def test_auth_config(self):
        """Test auth configuration"""
        auth_config = AuthConfig(type="bearer", bearer_token="test-token")
        assert auth_config.type == "bearer"
        assert auth_config.bearer_token == "test-token"
    
    def test_config_from_dict(self):
        """Test creating config from dictionary"""
        data = {
            "timeout": 60.0,
            "log_level": "DEBUG",
            "servers": {
                "test": {
                    "command": "echo",
                    "args": ["hello"]
                }
            }
        }
        
        config = Config.from_dict(data)
        assert config.timeout == 60.0
        assert config.log_level == "DEBUG"
        assert "test" in config.servers
    
    def test_config_to_dict(self):
        """Test converting config to dictionary"""
        config = Config()
        config.timeout = 45.0
        config.servers["test"] = ServerConfig(
            name="test",
            command="echo"
        )
        
        data = config.to_dict()
        assert data["timeout"] == 45.0
        assert "test" in data["servers"]


class TestToolRegistry:
    """Test tool registry functionality"""
    
    def test_tool_info_creation(self):
        """Test tool info creation"""
        tool_info = ToolInfo(
            name="test_tool",
            description="Test tool",
            server_name="test_server",
            input_schema={"type": "object"}
        )
        
        assert tool_info.name == "test_tool"
        assert tool_info.description == "Test tool"
        assert tool_info.server_name == "test_server"
        assert tool_info.permission == ToolPermission.ALLOW
    
    def test_tool_permission_determination(self):
        """Test tool permission determination"""
        config = Config()
        config.allowed_tools = ["fs.*"]
        config.blocked_tools = ["fs.delete"]
        
        registry = ToolRegistry(config)
        
        # Test allowed pattern
        assert registry._determine_tool_permission("fs_read") == ToolPermission.ALLOW
        
        # Test blocked pattern
        assert registry._determine_tool_permission("fs_delete") == ToolPermission.BLOCK
        
        # Test default (no allow patterns configured)
        config.allowed_tools = []
        registry = ToolRegistry(config)
        assert registry._determine_tool_permission("any_tool") == ToolPermission.ALLOW
    
    def test_metadata_extraction(self):
        """Test metadata extraction from descriptions"""
        registry = ToolRegistry(Config())
        
        # Test category extraction
        category, tags = registry._extract_metadata("Category: database. Tags: query, sql")
        assert category == "database"
        assert "query" in tags
        assert "sql" in tags
        
        # Test auto-categorization
        category, tags = registry._extract_metadata("Read a file from disk")
        assert category == "file"
        assert "file" in tags
    
    def test_tool_validation(self):
        """Test tool argument validation"""
        config = Config()
        registry = ToolRegistry(config)
        
        # Valid schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        # Valid arguments
        assert registry.validate_tool_arguments("test", {"name": "John", "age": 30})
        
        # Missing required field
        assert not registry.validate_tool_arguments("test", {"age": 30})
        
        # Wrong type
        assert not registry.validate_tool_arguments("test", {"name": 123})


class TestConnectionManager:
    """Test connection manager functionality"""
    
    @pytest.mark.asyncio
    async def test_connection_manager_creation(self):
        """Test connection manager creation"""
        config = Config()
        manager = MCPConnectionManager(config)
        
        assert manager.config == config
        assert len(manager.connections) == 0
        assert not manager._running
    
    @pytest.mark.asyncio
    async def test_connection_status(self):
        """Test connection status reporting"""
        config = Config()
        manager = MCPConnectionManager(config)
        
        status = await manager.get_connection_status()
        assert isinstance(status, dict)
    
    @pytest.mark.asyncio
    async def test_server_addition(self):
        """Test adding a server"""
        config = Config()
        manager = MCPConnectionManager(config)
        
        server_config = ServerConfig(
            name="test",
            command="echo",
            args=["hello"]
        )
        
        # This would normally connect, but we'll just test the config addition
        with patch.object(manager, '_connect_server', new_callable=AsyncMock):
            await manager.add_server("test", server_config)
            assert "test" in config.servers


class TestCodexClient:
    """Test main client functionality"""
    
    def test_client_creation(self):
        """Test client creation"""
        config = Config()
        client = CodexClient(config)
        
        assert client.config == config
        assert not client._initialized
        assert len(client._sessions) == 0
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization"""
        config = Config()
        client = CodexClient(config)
        
        # Mock the connection process
        with patch.object(client, '_connect_to_server', new_callable=AsyncMock):
            with patch.object(client.tool_registry, 'initialize', new_callable=AsyncMock):
                await client.initialize()
                assert client._initialized
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality"""
        config = Config()
        client = CodexClient(config)
        
        # Test when not initialized
        health = await client.health_check()
        assert health["status"] == "not_initialized"
        
        # Test when initialized but no connections
        client._initialized = True
        health = await client.health_check()
        assert health["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client context manager"""
        config = Config()
        
        async with CodexClient(config) as client:
            assert client is not None
        
        # Client should be closed after context exit
        assert not client._initialized


@pytest.mark.asyncio
async def test_example_workflow():
    """Test an example workflow"""
    config = Config()
    
    # Add a mock server
    config.servers["test"] = ServerConfig(
        name="test",
        command="echo",
        args=["hello"]
    )
    
    # Mock the session and tools
    with patch('codex_python.core.client.stdio_client') as mock_stdio:
        with patch('mcp.ClientSession') as mock_session_class:
            # Create mock session
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock()
            mock_session.list_tools = AsyncMock()
            mock_session.list_tools.return_value = MagicMock()
            mock_session.list_tools.return_value.tools = []
            mock_session.call_tool = AsyncMock()
            mock_session.call_tool.return_value = MagicMock()
            mock_session.call_tool.return_value.content = []
            
            mock_session_class.return_value = mock_session
            mock_stdio.return_value.__aenter__.return_value = (None, None)
            
            # Test the workflow
            async with CodexClient(config) as client:
                # List tools
                tools = await client.list_tools()
                assert isinstance(tools, list)
                
                # Health check
                health = await client.health_check()
                assert "status" in health
                
                # Server info
                info = await client.get_all_servers_info()
                assert isinstance(info, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])