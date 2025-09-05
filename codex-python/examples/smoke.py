import asyncio
import json
import os
from codex_python.core.config import Config
from codex_python.core.orchestrator import CodexOrchestrator


async def main():
    cfg = Config.from_env()
    orch = CodexOrchestrator(cfg)
    await orch.initialize()
    try:
        print("== HEALTH ==")
        print(json.dumps(await orch.mcp_client.health_check(), indent=2))

        print("\n== SEARCH ==")
        res = await orch.search_files("*.py", root_path=os.getcwd(), mode="glob")
        print(f"Found: {len(res.result) if res.success else 0}")

        print("\n== EXEC ==")
        exec_res = await orch.execute_command(["python", "--version"])
        print(exec_res.result.get("stdout"))

        print("\n== CHAT (no tools) ==")
        async for out in orch.chat(["Say hello in one sentence."], stream=False):
            if isinstance(out, dict):
                print(out.get("content", "").strip())
                break

    finally:
        await orch.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

