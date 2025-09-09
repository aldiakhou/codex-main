import asyncio
import os
import time
import uuid
from typing import Any, Dict

from .base import BaseAgentInterface
from ..core.models import AIAgentRequest
from mcp_agents_orchestrator.__main__ import (
    exec_approval_request,
    exec_command_begin,
    exec_command_output_delta,
    exec_command_end,
    apply_patch_approval_request,
    patch_apply_begin,
    patch_apply_end,
    get_submission_id_for_call,
    wait_for_decision,
)


class DemoExecPatchAgent(BaseAgentInterface):
    async def process(self, request: AIAgentRequest) -> Dict[str, Any]:
        cwd = request.cwd or os.getcwd()
        # --- Exec demo ---
        exec_call = f"exec_{uuid.uuid4().hex[:8]}"
        exec_approval_request(exec_call, ["echo", "Hello from demo agent"], cwd, reason="demo exec")
        # Wait for approval decision
        sub_id = get_submission_id_for_call(exec_call)
        decision = wait_for_decision(sub_id or "", 120.0)
        if decision not in ("approved", "approved_for_session"):
            return {"success": False, "stage": "exec", "decision": decision or "timeout"}
        # Stream command output
        exec_command_begin(exec_call, ["echo", "Hello from demo agent"], cwd)
        exec_command_output_delta(exec_call, "stdout", b"Hello from demo agent\n")
        exec_command_end(exec_call, 0, stdout="Hello from demo agent\n", stderr="", formatted_output="Hello from demo agent\n", duration_ms=50)

        # --- Patch demo ---
        patch_call = f"patch_{uuid.uuid4().hex[:8]}"
        changes = {
            os.path.join(cwd, "DEMO_OUTPUT.txt"): {"Add": {"content": "Demo file created by agent\n"}}
        }
        apply_patch_approval_request(patch_call, changes, reason="demo patch")
        sub_id2 = get_submission_id_for_call(patch_call)
        decision2 = wait_for_decision(sub_id2 or "", 120.0)
        if decision2 not in ("approved", "approved_for_session"):
            return {"success": False, "stage": "patch", "decision": decision2 or "timeout"}
        patch_apply_begin(patch_call, changes, auto_approved=False)
        # Simulate apply success (real write is performed by Codex after approval in a full integration)
        patch_apply_end(patch_call, True, stdout="Applied 1 file", stderr="")

        return {
            "success": True,
            "exec": {"call_id": exec_call, "decision": decision},
            "patch": {"call_id": patch_call, "decision": decision2},
        }

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "name": "Demo Exec+Patch Agent",
            "description": "Demonstrates exec + patch approvals with streaming",
            "capabilities": ["exec", "patch"],
        }


def create_demo_exec_patch_agent() -> DemoExecPatchAgent:
    return DemoExecPatchAgent()

