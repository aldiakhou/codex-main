# Cadenza (Python)

A Python implementation of an MCP client/orchestrator, providing a robust and secure way to interact with MCP servers.

## Features

- **Multiple Transport Support**: Supports stdio, SSE, and HTTP transports
- **Tool Management**: Comprehensive tool registry with security controls
- **Connection Management**: Automatic connection handling and health checks
- **Authentication**: OAuth 2.0 and bearer token support
- **Security**: Tool sandboxing and permission controls
- **CLI Interface**: Full-featured command-line interface
- **Async Support**: Built with asyncio for high performance

## Installation

```bash
# Install from source
git clone <repository-url>
cd codex-python
pip install -e .

# Or install with pip (when published)
pip install codex-python
```

## Quick Start

### Configuration

Create a configuration file `codex.json`:

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"],
      "transport": "stdio"
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "transport": "stdio",
      "env": {
        "GITHUB_TOKEN": "your-github-token"
      }
    }
  },
  "timeout": 30.0,
  "log_level": "INFO",
  "enable_sandbox": true,
  "allowed_tools": ["fs.*", "github.*"],
  "blocked_tools": ["fs.delete"]
}
```

### Basic Usage

```python
import asyncio
from codex_python import CodexClient, Config

async def main():
    # Load configuration
    config = Config.from_file("codex.json")
    
    # Create client
    async with CodexClient(config) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {len(tools)}")
        
        # Call a tool
        result = await client.call_tool("fs_read_file", {"path": "example.txt"})
        print(f"Result: {result.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### CLI Usage

```bash
# List configured servers
cadenza list-servers

# List available tools
cadenza list-tools

# Call a tool
cadenza call-tool fs_read_file path=example.txt

# Check health
cadenza health

# Show status
cadenza status --format json
```

## Configuration

### Server Configuration

Servers can be configured with various transport options:

```json
{
  "servers": {
    "stdio-server": {
      "command": "python",
      "args": ["server.py"],
      "transport": "stdio",
      "env": {
        "API_KEY": "secret"
      }
    },
    "http-server": {
      "transport": "streamable_http",
      "url": "http://localhost:3000/mcp",
      "timeout": 60.0
    }
  }
}
```

### Authentication

#### OAuth 2.0

```json
{
  "auth": {
    "type": "oauth",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "token_url": "https://auth.example.com/token",
    "scopes": ["read", "write"]
  }
}
```

#### Bearer Token

```json
{
  "auth": {
    "type": "bearer",
    "bearer_token": "your-token"
  }
}
```

### Security Configuration

```json
{
  "enable_sandbox": true,
  "allowed_tools": ["fs.*", "github.*"],
  "blocked_tools": ["fs.delete", "system.exec"],
  "tool_timeout": 60.0,
  "max_concurrent_tools": 10
}
```

## API Reference

### CodexClient

The main client class for interacting with MCP servers.

```python
async with CodexClient(config) as client:
    # List tools
    tools = await client.list_tools()
    
    # Call tool
    result = await client.call_tool("tool_name", {"arg": "value"})
    
    # Stream results
    async for content in client.stream_tool_call("tool_name", {"arg": "value"}):
        print(content)
    
    # Health check
    health = await client.health_check()
```

### Tool Registry

The tool registry provides security controls and management:

```python
# Check if tool is allowed
if client.tool_registry.is_tool_allowed("tool_name"):
    # Use tool
    pass

# Get tool information
tool_info = client.tool_registry.get_tool_info("tool_name")
print(f"Category: {tool_info.category}")
print(f"Tags: {tool_info.tags}")

# List tools by category
tools = client.tool_registry.list_tools(category="file")
```

### Connection Manager

Manages connections to multiple servers:

```python
# Get connection status
status = await client.connection_manager.get_connection_status()

# Reconnect to a server
await client.connection_manager.reconnect_server("server_name")

# Get healthy sessions
sessions = await client.connection_manager.get_healthy_sessions()
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd codex-python

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=codex_python

# Run specific test
pytest tests/test_client.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
pyright
```

## Security Considerations

- **Tool Permissions**: Use allowed_tools and blocked_tools to restrict access
- **Sandboxing**: Enable sandbox mode for potentially dangerous tools
- **Authentication**: Use proper authentication for sensitive operations
- **Environment Variables**: Store secrets in environment variables, not config files
- **Network Security**: Use HTTPS for HTTP transports in production

## Examples

### File Operations

```python
# Read a file
result = await client.call_tool("fs_read_file", {"path": "example.txt"})

# Write a file
result = await client.call_tool("fs_write_file", {
    "path": "output.txt",
    "content": "Hello, World!"
})
```

### GitHub Integration

```python
# List repositories
result = await client.call_tool("github_list_repositories", {
    "owner": "username"
})

# Create an issue
result = await client.call_tool("github_create_issue", {
    "owner": "username",
    "repo": "repository",
    "title": "Issue title",
    "body": "Issue description"
})
```

### Web Operations

```python
# Fetch a webpage
result = await client.call_tool("fetch", {
    "url": "https://example.com"
})

# Send HTTP request
result = await client.call_tool("http_request", {
    "url": "https://api.example.com/data",
    "method": "GET"
})
```

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check server command and args
2. **Authentication Failed**: Verify tokens and credentials
3. **Tool Not Found**: Check tool name and server configuration
4. **Permission Denied**: Check allowed_tools and blocked_tools

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or via CLI:

```bash
cadenza --log-level DEBUG list-tools
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Ensure code quality checks pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: <docs-url>
- Discussions: <discussions-url>
