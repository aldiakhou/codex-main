"""
Example usage of Codex Python
"""

import asyncio
import json
from pathlib import Path

from codex_python import CodexClient, Config


async def main():
    """Example usage of Codex Python"""
    
    # Create a simple configuration
    config = Config()
    
    # Add a filesystem server (example)
    config.servers["filesystem"] = Config.ServerConfig(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", str(Path.cwd())],
        transport="stdio"
    )
    
    # Create client
    async with CodexClient(config) as client:
        print("=== Codex Python Example ===")
        
        # Check health
        health = await client.health_check()
        print(f"Health status: {health['status']}")
        
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {len(tools)}")
        
        for tool in tools[:5]:  # Show first 5 tools
            print(f"  - {tool.name}: {tool.description[:50]}...")
        
        # Example tool call (if filesystem tools are available)
        if any("filesystem" in tool.name.lower() for tool in tools):
            try:
                # Create a test file
                result = await client.call_tool("fs_write_file", {
                    "path": "test_output.txt",
                    "content": "Hello from Codex Python!"
                })
                print(f"Write result: {result.content}")
                
                # Read the file back
                result = await client.call_tool("fs_read_file", {
                    "path": "test_output.txt"
                })
                print(f"Read result: {result.content}")
                
            except Exception as e:
                print(f"Tool call failed: {e}")
        
        # Show server information
        servers_info = await client.get_all_servers_info()
        print(f"\nConnected servers: {len(servers_info)}")
        
        for server_name, info in servers_info.items():
            print(f"  {server_name}: {info.get('status', 'unknown')}")


if __name__ == "__main__":
    asyncio.run(main())