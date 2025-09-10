import sys, asyncio
sys.path.insert(0, __package__ or __name__)
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.mcp_client import PocketFlowMCPClient

cfg = {"command":"python", "args":["-m","mcp_server_fetch"], "type":"stdio"}
client = PocketFlowMCPClient(cfg)

async def main():
    tools = await client.list_tools_atomic()
    print('TOOLS_COUNT:', len(tools))
    for t in tools:
        print('TOOL:', t)

if __name__ == '__main__':
    asyncio.run(main())

