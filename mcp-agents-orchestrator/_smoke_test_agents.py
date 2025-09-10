import sys, asyncio, os
sys.path.insert(0, os.path.dirname(__file__))

from agents.base import get_agent_registry
from agents.mcp_enhanced_agents import register_mcp_agents
from core.models import AIAgentRequest


async def run_once(agent_id: str, ctx: dict):
    reg = get_agent_registry()
    register_mcp_agents(reg)
    req = AIAgentRequest(text=ctx.get('text',''), context=ctx, cwd=os.getcwd())
    try:
        res = await reg.process_request(agent_id, req)
        print(f"AGENT {agent_id} OK: {str(res)[:300]}")
    except Exception as e:
        print(f"AGENT {agent_id} ERR: {e}")


async def main():
    # Use permissive stdio by default (leave unset to default '*')
    tasks = [
        run_once('web_search', {'query':'senegal vs congo score today','max_results':5}),
        run_once('deep_research', {'topic':'Senegal vs Congo match result','depth':'brief'}),
        run_once('rag', {'query':'What is RAG?','max_results':3}),
    ]
    for coro in tasks:
        await coro

if __name__ == '__main__':
    asyncio.run(main())

