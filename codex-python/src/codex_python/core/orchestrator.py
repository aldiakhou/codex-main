"""
Core orchestrator for Codex Python
Integrates LLM client, MCP, tools, sandboxing, and approval systems
"""

import asyncio
import json
import os
import structlog
from typing import Dict, List, Optional, Any, AsyncIterator, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time

from .config import Config
from .client import CodexClient
from ..llm.client import (
    LLMClient,
    LLMConfig,
    LLMMessage,
    LLMTool,
    LLMManager,
    create_llm_client,
    LLMProvider,
)
from ..auth.store import load_api_key
from ..sandbox.executor import SandboxExecutor, SandboxConfig, SandboxPolicy, SandboxLevel
from ..search.file_searcher import SearchManager, SearchQuery, SearchConfig, SearchResult
from ..patch.applier import PatchManager, PatchConfig, Patch, PatchParser
from ..exec_policy.engine import PolicyManager, ExecutionContext, PolicyEvaluation, PolicyDecision
from ..approval.system import ApprovalManager, ApprovalContext, ApprovalLevel, ApprovalStatus
from ..mcp.tool_registry import ToolRegistry, ToolInfo
from .exec_session import ExecSessionManager
from .exec_mux import LocalExecMux
from .turn_diff_tracker import build_snapshot as td_snapshot, diff_snapshots as td_diff
from ..utils.history import append_event
from ..utils.events import EventBus

logger = structlog.get_logger(__name__)


class CodexOperation(Enum):
    """Types of operations Codex can perform"""
    CHAT = "chat"
    COMMAND = "command"
    SEARCH = "search"
    PATCH = "patch"
    TOOL_CALL = "tool_call"
    FILE_OPERATION = "file_operation"


@dataclass
class OperationResult:
    """Result of a Codex operation"""
    operation: CodexOperation
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodexSession:
    """User session with Codex"""
    id: str
    created_at: float
    last_activity: float
    working_directory: str
    user: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodexOrchestrator:
    """Main orchestrator for Codex Python - integrates all components"""
    
    def __init__(self, config: Config):
        self.config = config
        self.sessions: Dict[str, CodexSession] = {}
        
        # Initialize components
        self.llm_manager = LLMManager()
        self.mcp_client = CodexClient(config)
        self.search_manager = SearchManager()
        self.patch_manager = PatchManager()
        self.policy_manager = PolicyManager()
        self.approval_manager = ApprovalManager()
        self._exec_sessions = ExecSessionManager()
        
        # Sandbox configuration (map config.sandbox_mode)
        default_level = SandboxLevel.WORKSPACE
        enabled = config.enable_sandbox
        mode = getattr(config, 'sandbox_mode', 'workspace')
        if isinstance(mode, str):
            m = mode.lower().replace('_', '-')
            if m in ("read-only", "readonly", "read_only"):
                default_level = SandboxLevel.READ_ONLY
            elif m in ("workspace-write", "workspace", "workspace_write"):
                default_level = SandboxLevel.WORKSPACE
            elif m in ("danger-full-access", "danger", "danger_full_access"):
                enabled = False
        self.sandbox_config = SandboxConfig(
            enabled=enabled,
            default_level=default_level,
            strict_mode=True
        )
        self.sandbox_executor = SandboxExecutor(self.sandbox_config)

        # Operation history
        self.operation_history: List[OperationResult] = []

        # Session-scoped writable roots for patches/commands (auto-approval scope)
        self._session_writable_roots: Dict[str, set] = {}
        
        # Event bus
        self.events = EventBus()

        # Initialize
        self._initialized = False
        self.shared_plan: List[Dict[str, Any]] = []
    
    async def initialize(self) -> None:
        """Initialize all components"""
        if self._initialized:
            return
        
        logger.info("Initializing Codex orchestrator")
        
        # Initialize LLM manager with configured providers
        await self._initialize_llm_clients()
        
        # Initialize MCP client
        await self.mcp_client.initialize()
        
        # Initialize policy manager with default policies
        await self.policy_manager.initialize()
        
        # Initialize approval manager with default policies
        self.approval_manager.load_default_policies()
        # Bridge approval requests to event bus
        try:
            self.approval_manager.add_listener(lambda req: asyncio.create_task(self.events.publish(
                "approval_request",
                id=req.id,
                operation=req.operation,
                description=req.description,
                requester=req.requester,
                session_id=req.session_id,
                timeout_s=req.timeout,
                details=req.details,
            )))
        except Exception:
            pass
        
        self._initialized = True
        logger.info("Codex orchestrator initialized successfully")

        # Start local exec multiplexer (cross-process control)
        try:
            enable_mux = True
            if hasattr(self.config, 'enable_exec_mux'):
                enable_mux = bool(getattr(self.config, 'enable_exec_mux'))
            if enable_mux:
                async def _write_cb(session_id: str, data: bytes):
                    # Use write_stdin path (binary-safe)
                    await self._exec_sessions.write_stdin(session_id, data.decode(errors='ignore'))

                async def _stop_cb(session_id: str):
                    await self._exec_sessions.stop_session(session_id)

                import secrets
                token = getattr(self.config, 'exec_mux_token', None) or secrets.token_urlsafe(24)
                self._exec_mux = LocalExecMux(_write_cb, _stop_cb, token=token)
                port = await self._exec_mux.start()
                try:
                    # Persist port+token to ~/.codex/execmux.json
                    from ..auth.store import codex_home_dir
                    p = codex_home_dir() / "execmux.json"
                    p.write_text(json.dumps({"port": port, "token": token}), encoding='utf-8')
                except Exception:
                    pass
        except Exception:
            pass
    
    async def _initialize_llm_clients(self) -> None:
        """Initialize LLM clients based on configuration"""
        
        # Add OpenAI client if configured
        api_key = getattr(self.config, 'openai_api_key', None) or load_api_key()
        if api_key:
            openai_config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=getattr(self.config, 'openai_model', 'gpt-4'),
                api_key=api_key,
                max_tokens=getattr(self.config, 'max_tokens', 4096),
                temperature=getattr(self.config, 'temperature', 0.7),
                use_responses_api=getattr(self.config, 'openai_use_responses_api', False),
            )
            self.llm_manager.add_client("openai", create_llm_client(openai_config), is_default=True)
        
        # Add Ollama client if configured
        if hasattr(self.config, 'ollama_url') and self.config.ollama_url:
            ollama_config = LLMConfig(
                provider=LLMProvider.OLLAMA,
                model=getattr(self.config, 'ollama_model', 'llama2'),
                base_url=self.config.ollama_url,
                max_tokens=getattr(self.config, 'max_tokens', 4096),
                temperature=getattr(self.config, 'temperature', 0.7)
            )
            self.llm_manager.add_client("ollama", create_llm_client(ollama_config))
    
    def create_session(self, session_id: str, working_directory: str, user: Optional[str] = None) -> CodexSession:
        """Create a new Codex session"""
        session = CodexSession(
            id=session_id,
            created_at=time.time(),
            last_activity=time.time(),
            working_directory=working_directory,
            user=user
        )
        
        self.sessions[session_id] = session
        
        # Initialize approval session
        self.approval_manager.create_session(session_id)
        
        # Initialize policy session
        self.policy_manager.create_session(session_id)
        
        logger.info("Created session", session_id=session_id, user=user)
        return session
    
    def get_session(self, session_id: str) -> Optional[CodexSession]:
        """Get existing session"""
        session = self.sessions.get(session_id)
        if session:
            session.last_activity = time.time()
        return session
    
    def close_session(self, session_id: str) -> None:
        """Close a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        # Close approval session
        self.approval_manager.close_session(session_id)
        
        # Close policy session
        self.policy_manager.close_session(session_id)
        
        logger.info("Closed session", session_id=session_id)
    
    async def chat(
        self,
        messages: List[Union[str, Dict, LLMMessage]],
        session_id: Optional[str] = None,
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False
    ) -> AsyncIterator[Union[str, Dict]]:
        """Chat with LLM, optionally with tool use.

        - When stream=False: yields a few dict snapshots per loop step and finishes with final result.
        - When stream=True: yields {type: 'delta', content: ...} chunks between tool calls, then tool results, until completion.
        """
        
        if not self._initialized:
            await self.initialize()
        
        # Get session
        session = self.get_session(session_id) if session_id else None
        working_dir = session.working_directory if session else str(Path.cwd())
        
        # Prepare messages
        normalized_messages = []
        for msg in messages:
            if isinstance(msg, str):
                normalized_messages.append(LLMMessage(role="user", content=msg))
            elif isinstance(msg, dict):
                normalized_messages.append(LLMMessage(**msg))
            else:
                normalized_messages.append(msg)
        
        # Add system message with context
        system_context = self._build_system_context(working_dir, session)
        normalized_messages.insert(0, LLMMessage(role="system", content=system_context))
        
        # Get available tools if not provided
        if tools is None:
            tools = await self._get_available_tools(session_id)
        
        # Tool-calling loop (bounded)
        max_steps = 4
        step = 0
        final_response: Optional[str] = None
        while True:
            if stream:
                # Stream deltas until a tool call shows up or completion
                content_accum = ""
                tool_calls = []
                async for chunk in await self.llm_manager.chat(normalized_messages, tools=tools, stream=True):
                    if chunk.tool_calls:
                        tool_calls = chunk.tool_calls
                        if content_accum:
                            yield {"type": "delta", "content": content_accum, "step": step}
                            content_accum = ""
                        break
                    if chunk.content:
                        content_accum = chunk.content
                        yield {"type": "delta", "content": content_accum, "step": step}
                    # Propagate reasoning deltas when available
                    if getattr(chunk, "reasoning_raw_delta", None):
                        yield {"type": "reasoning_raw_delta", "content": chunk.reasoning_raw_delta, "step": step}
                    if getattr(chunk, "reasoning_delta", None):
                        yield {"type": "reasoning_delta", "content": chunk.reasoning_delta, "step": step}
                    # Propagate tool result deltas from provider, when available
                    if getattr(chunk, "tool_result_delta", None):
                        yield {"type": "tool_result", "content": chunk.tool_result_delta, "step": step}
                if not tool_calls:
                    # No tools requested => done
                    yield {"content": content_accum, "tool_calls": []}
                    final_response = content_accum
                    break
            else:
                response = await self.llm_manager.chat(normalized_messages, tools=tools, stream=False)
                if response.content:
                    yield {"content": response.content, "step": step}
                    final_response = response.content
                if getattr(response, "tool_result_delta", None):
                    yield {"type": "tool_result", "content": response.tool_result_delta, "step": step}
                if not response.tool_calls:
                    yield {"content": response.content, "usage": response.usage, "tool_calls": []}
                    break
                tool_calls = response.tool_calls

            # Execute tool calls and append tool messages
            for call in tool_calls:
                tool_name = call.name
                args = call.arguments or {}
                tool_output_text = ""
                try:
                    if stream:
                        # notify UI about tool start and publish event
                        yield {"type": "tool_start", "name": tool_name}
                        try:
                            await self.events.publish("tool_start", name=tool_name)
                        except Exception:
                            pass
                    # Built-in tools
                    if tool_name in {"local_shell", "apply_patch", "file_search"}:
                        result = await self.execute_builtin_tool(tool_name, args, session_id=session_id)
                        tool_output_text = json.dumps(result, ensure_ascii=False)
                    else:
                        # MCP tools via client
                        mcp_result = await self.mcp_client.call_tool(tool_name, args)
                        parts = []
                        for c in getattr(mcp_result, "content", []) or []:
                            if hasattr(c, "text") and c.text:
                                parts.append(c.text)
                            elif hasattr(c, "uri") and c.uri:
                                parts.append(f"[resource] {c.uri}")
                            elif hasattr(c, "data") and c.data:
                                parts.append(f"[binary {len(c.data)} bytes]")
                        tool_output_text = "\n".join(parts) if parts else "(no content)"
                except Exception as e:
                    tool_output_text = f"[tool_error] {e}"

                normalized_messages.append(LLMMessage(role="tool", content=tool_output_text, tool_call_id=call.id))

                if stream:
                    # notify UI about tool end and publish event
                    # also surface tool result payload for consumers
                    try:
                        yield {"type": "tool_result", "name": tool_name, "content": tool_output_text}
                    except Exception:
                        pass
                    yield {"type": "tool_end", "name": tool_name}
                    try:
                        await self.events.publish("tool_end", name=tool_name)
                    except Exception:
                        pass

            step += 1
            if step >= max_steps:
                yield {"content": "[tool loop limit reached]", "tool_calls": []}
                break

        # Notifier hook
        try:
            if getattr(self.config, 'notify', None):
                import asyncio.subprocess as asp
                args = list(self.config.notify)
                payload = json.dumps({"type": "agent-turn-complete", "timestamp": time.time()})
                if args:
                    args = args + [payload]
                    await asp.create_subprocess_exec(*args)
        except Exception:
            pass
    
    async def execute_command(
        self,
        command: List[str],
        session_id: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        require_approval: bool = True
    ) -> OperationResult:
        """Execute a command with safety checks and approval"""
        
        start_time = time.time()
        
        try:
            # Get session
            session = self.get_session(session_id) if session_id else None
            working_dir = cwd or (session.working_directory if session else str(Path.cwd()))

            # Take a pre-exec snapshot to compute a TurnDiff afterwards
            try:
                ignore = list(getattr(self.config, 'diff_ignore', []))
                # Merge language-specific ignores
                langs = getattr(self.config, 'project_languages', []) or []
                lang_map = getattr(self.config, 'diff_ignore_by_language', {}) or {}
                for lang in langs:
                    ignore.extend(lang_map.get(lang, []))
                pre_snapshot = td_snapshot(
                    working_dir,
                    ignore=ignore,
                    hash_limit_bytes=getattr(self.config, 'diff_hash_limit_bytes', 128 * 1024),
                    max_files=getattr(self.config, 'diff_max_files', 5000),
                    file_size_limit_bytes=getattr(self.config, 'diff_file_size_limit_bytes', 10 * 1024 * 1024),
                )
            except Exception:
                pre_snapshot = None

            # Create execution context
            context = ExecutionContext(
                command=command,
                working_directory=working_dir,
                environment=env or {},
                user=session.user if session else None,
                session_id=session_id,
                source="user"  # Could be "ai" for AI-generated commands
            )
            
            # Evaluate against policies
            policy_result = await self.policy_manager.evaluate_command(context)
            
            # Map config approval_policy into behavior
            approval_mode = getattr(self.config, "approval_policy", "on_request").lower()
            # Whether to ask before initial run
            ask_before = (
                (approval_mode == "on_request" and policy_result.decision in [PolicyDecision.REQUIRE_APPROVAL, PolicyDecision.DENY])
                or (approval_mode == "unless_trusted" and not self.policy_manager.engine.is_known_safe_command(command))
                or (approval_mode == "never" and False)
            )

            if require_approval and ask_before:
                approval_context = ApprovalContext(
                    operation="command_execution",
                    description=f"Execute command: {' '.join(command)}",
                    details={
                        "command": command,
                        "working_directory": working_dir,
                        "policy_decision": policy_result.decision.value,
                        "policy_reasons": policy_result.reasons
                    },
                    requester=session.user if session else "unknown",
                    session_id=session_id,
                    source=context.source,
                    risk_score=1.0 - policy_result.confidence
                )
                
                approval_response = await self.approval_manager.request_approval(approval_context)
                
                if approval_response.status != ApprovalStatus.APPROVED:
                    return OperationResult(
                        operation=CodexOperation.COMMAND,
                        success=False,
                        error=f"Command not approved: {approval_response.reason}",
                        execution_time=time.time() - start_time,
                        metadata={"approval_response": approval_response.__dict__}
                    )
            
            # Execute command with sandbox
            sandbox_policy = self.sandbox_executor._create_default_policy()
            
            # Adjust sandbox level based on policy
            if policy_result.decision == PolicyDecision.SANDBOX:
                sandbox_policy.level = SandboxLevel.RESTRICTED
            
            # Publish begin event
            try:
                await self.events.publish("exec_begin", call_id=f"exec_{int(time.time()*1000)}", command=command, cwd=working_dir)
            except Exception:
                pass

            # Initial run (sandboxed by default; restricted if policy says so)
            result = await self.sandbox_executor.execute_command(
                command,
                cwd=working_dir,
                env=env,
                policy=sandbox_policy
            )
            
            # Emit a post-exec TurnDiff if possible
            try:
                if pre_snapshot is not None:
                    ignore = list(getattr(self.config, 'diff_ignore', []))
                    langs = getattr(self.config, 'project_languages', []) or []
                    lang_map = getattr(self.config, 'diff_ignore_by_language', {}) or {}
                    for lang in langs:
                        ignore.extend(lang_map.get(lang, []))
                    post_snapshot = td_snapshot(
                        working_dir,
                        ignore=ignore,
                        hash_limit_bytes=getattr(self.config, 'diff_hash_limit_bytes', 128 * 1024),
                        max_files=getattr(self.config, 'diff_max_files', 5000),
                        file_size_limit_bytes=getattr(self.config, 'diff_file_size_limit_bytes', 10 * 1024 * 1024),
                    )
                    diff = td_diff(pre_snapshot, post_snapshot)
                    await self.events.publish("turn_diff", files=diff)
            except Exception:
                pass

            op_result = OperationResult(
                operation=CodexOperation.COMMAND,
                success=result.get("success", False),
                result=result,
                execution_time=time.time() - start_time,
                metadata={
                    "sandboxed": result.get("sandboxed", False),
                    "policy_evaluation": policy_result.__dict__
                }
            )

            try:
                await self.events.publish("exec_end", call_id="", exit_code=op_result.result.get("returncode") if isinstance(op_result.result, dict) else None, success=op_result.success)
            except Exception:
                pass

            # On-failure escalation path
            if (
                not op_result.success
                and approval_mode == "on_failure"
                and require_approval
            ):
                approval_context = ApprovalContext(
                    operation="command_execution",
                    description=f"Retry without sandbox: {' '.join(command)}",
                    details={
                        "command": command,
                        "working_directory": working_dir,
                        "previous_error": result.get("stderr") or result.get("stdout"),
                    },
                    requester=session.user if session else "unknown",
                    session_id=session_id,
                    source=context.source,
                    risk_score=0.9,
                )
                approval_response = await self.approval_manager.request_approval(approval_context)
                if approval_response.status == ApprovalStatus.APPROVED:
                    # Retry with FULL policy
                    retry_policy = self.sandbox_executor._create_default_policy()
                    retry_policy.level = SandboxLevel.FULL
                    retry_result = await self.sandbox_executor.execute_command(
                        command, cwd=working_dir, env=env, policy=retry_policy
                    )
                    op_result = OperationResult(
                        operation=CodexOperation.COMMAND,
                        success=retry_result.get("success", False),
                        result=retry_result,
                        execution_time=time.time() - start_time,
                        metadata={
                            "sandboxed": retry_result.get("sandboxed", False),
                            "escalated": True,
                        },
                    )

            # History log
            if getattr(self.config, "history_enabled", True):
                try:
                    append_event(
                        {
                            "type": "exec",
                            "command": command,
                            "cwd": working_dir,
                            "success": op_result.success,
                            "returncode": op_result.result.get("returncode") if isinstance(op_result.result, dict) else None,
                            "ts": time.time(),
                        },
                        path=getattr(self.config, "history_path", None),
                    )
                except Exception:
                    pass

            return op_result
            
        except Exception as e:
            logger.error("Command execution failed", command=command, error=str(e))
            return OperationResult(
                operation=CodexOperation.COMMAND,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def execute_command_stream(
        self,
        command: List[str],
        session_id: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        require_approval: bool = True,
        max_deltas: int = 10_000,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream command output with safety checks and optional approval."""
        # Evaluate policy same as execute_command but stream deltas
        session = self.get_session(session_id) if session_id else None
        working_dir = cwd or (session.working_directory if session else str(Path.cwd()))

        context = ExecutionContext(
            command=command,
            working_directory=working_dir,
            environment=env or {},
            user=session.user if session else None,
            session_id=session_id,
            source="user",
        )
        policy_result = await self.policy_manager.evaluate_command(context)

        if require_approval and policy_result.decision in [PolicyDecision.REQUIRE_APPROVAL, PolicyDecision.DENY]:
            approval_context = ApprovalContext(
                operation="command_execution_stream",
                description=f"Execute command (stream): {' '.join(command)}",
                details={
                    "command": command,
                    "working_directory": working_dir,
                    "policy_decision": policy_result.decision.value,
                    "policy_reasons": policy_result.reasons,
                },
                requester=session.user if session else "unknown",
                session_id=session_id,
                source=context.source,
                risk_score=1.0 - policy_result.confidence,
            )
            approval_response = await self.approval_manager.request_approval(approval_context)
            if approval_response.status != ApprovalStatus.APPROVED:
                yield {"type": "error", "message": f"Command not approved: {approval_response.reason}"}
                return

        # Default sandbox policy, possibly use restricted if indicated
        sandbox_policy = self.sandbox_executor._create_default_policy()
        if policy_result.decision == PolicyDecision.SANDBOX:
            sandbox_policy.level = SandboxLevel.RESTRICTED

        call_id = f"exec_{int(time.time()*1000)}"
        try:
            await self.events.publish("exec_begin", call_id=call_id, command=command, cwd=working_dir)
        except Exception:
            pass

        async for item in self.sandbox_executor.execute_command_stream(
            command,
            cwd=working_dir,
            env=env,
            policy=sandbox_policy,
            max_deltas=max_deltas,
        ):
            if item.get("type") == "delta":
                try:
                    await self.events.publish("exec_output_delta", call_id=call_id, stream=item.get("stream"))
                except Exception:
                    pass
            elif item.get("type") == "result":
                try:
                    await self.events.publish("exec_end", call_id=call_id, exit_code=item.get("returncode"), success=(item.get("returncode", 1) == 0))
                except Exception:
                    pass
            yield item
    
    async def search_files(
        self,
        pattern: str,
        session_id: Optional[str] = None,
        root_path: Optional[str] = None,
        **kwargs
    ) -> OperationResult:
        """Search for files"""
        
        start_time = time.time()
        
        try:
            # Get session
            session = self.get_session(session_id) if session_id else None
            search_root = root_path or (session.working_directory if session else str(Path.cwd()))
            
            # Create search query (normalize mode if provided)
            mode_arg = kwargs.pop("mode", None)
            if isinstance(mode_arg, str):
                try:
                    from ..search.file_searcher import SearchMode
                    kwargs["mode"] = SearchMode(mode_arg)
                except Exception:
                    pass
            query = SearchQuery(pattern=pattern, root_path=search_root, **kwargs)
            
            # Execute search
            results = await self.search_manager.search(query, search_id=session_id)
            
            return OperationResult(
                operation=CodexOperation.SEARCH,
                success=True,
                result=results,
                execution_time=time.time() - start_time,
                metadata={
                    "query": query.__dict__,
                    "result_count": len(results)
                }
            )
            
        except Exception as e:
            logger.error("Search failed", pattern=pattern, error=str(e))
            return OperationResult(
                operation=CodexOperation.SEARCH,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def apply_patch(
        self,
        patch_text: str,
        session_id: Optional[str] = None,
        root_path: Optional[str] = None,
        require_approval: bool = True
    ) -> OperationResult:
        """Apply a patch"""
        
        start_time = time.time()
        
        try:
            # Get session
            session = self.get_session(session_id) if session_id else None
            patch_root = root_path or (session.working_directory if session else str(Path.cwd()))
            
            # Analyze patch to collect touched paths and suggest writable root
            try:
                patch_obj = PatchParser.parse_unified_diff(patch_text)
            except Exception:
                patch_obj = None

            changed_paths = []
            if patch_obj:
                for fp in patch_obj.patches:
                    if fp.new_path:
                        changed_paths.append(fp.new_path)
                    if fp.old_path:
                        changed_paths.append(fp.old_path)

            suggested_root = patch_root
            if changed_paths:
                # Compute shallow common prefix under patch_root
                abs_paths = [str(Path(patch_root) / Path(p).as_posix()) for p in changed_paths]
                try:
                    common = os.path.commonpath(abs_paths)
                    suggested_root = common
                except Exception:
                    suggested_root = patch_root

            # Auto-approve if all changes are within previously granted roots for this session
            session_roots = self._session_writable_roots.get(session_id or "", set())
            within_granted = False
            if session_roots and changed_paths:
                within_granted = all(any((Path(patch_root) / p).resolve().as_posix().startswith(Path(r).resolve().as_posix()) for r in session_roots) for p in changed_paths)

            # Check if approval is required (skip if within granted roots)
            if require_approval and not within_granted:
                approval_context = ApprovalContext(
                    operation="patch_application",
                    description="Apply patch to codebase",
                    details={
                        "patch_size": len(patch_text),
                        "root_path": patch_root,
                        "changed_paths": changed_paths,
                        "suggested_grant_root": suggested_root,
                    },
                    requester=session.user if session else "unknown",
                    session_id=session_id,
                    source="user",
                    risk_score=0.7  # Patches are medium risk
                )

                approval_response = await self.approval_manager.request_approval(approval_context)

                if approval_response.status != ApprovalStatus.APPROVED:
                    return OperationResult(
                        operation=CodexOperation.PATCH,
                        success=False,
                        error=f"Patch not approved: {approval_response.reason}",
                        execution_time=time.time() - start_time,
                        metadata={"approval_response": approval_response.__dict__}
                    )

                # If approved, record session-granted root to auto-approve future patches in same area
                if session_id:
                    roots = self._session_writable_roots.setdefault(session_id, set())
                    if suggested_root:
                        roots.add(str(Path(suggested_root).resolve()))
            
            # Apply patch
            call_id = f"patch_{int(time.time()*1000)}"
            try:
                await self.events.publish("patch_begin", call_id=call_id)
            except Exception:
                pass
            result = await self.patch_manager.apply_patch_text(patch_text, patch_root)
            # Publish a minimal TurnDiff summary for UI
            try:
                files = []
                if patch_obj:
                    for fp in patch_obj.patches:
                        path_new = (fp.new_path or "").strip()
                        path_old = (fp.old_path or "").strip()
                        added = 0
                        removed = 0
                        for h in fp.hunks:
                            for ln in h.lines:
                                if ln.startswith('+') and not ln.startswith('+++'):
                                    added += 1
                                elif ln.startswith('-') and not ln.startswith('---'):
                                    removed += 1
                        status = "modified"
                        if fp.operation.name.lower() == "add":
                            status = "added"
                        elif fp.operation.name.lower() == "delete":
                            status = "deleted"
                        elif fp.operation.name.lower() == "move" or (path_old and path_new and path_old != path_new):
                            status = "renamed"
                        files.append({
                            "path": path_new or path_old,
                            "status": status,
                            "from": path_old if status == "renamed" else None,
                            "to": path_new if status == "renamed" else None,
                            "added": added,
                            "removed": removed,
                        })
                await self.events.publish("turn_diff", files=files)
            except Exception:
                pass
            try:
                await self.events.publish("patch_end", call_id=call_id, success=result.success)
            except Exception:
                pass
            
            return OperationResult(
                operation=CodexOperation.PATCH,
                success=result.success,
                result=result,
                execution_time=time.time() - start_time,
                metadata={
                    "applied_patches": len(result.applied_patches),
                    "failed_patches": len(result.failed_patches)
                }
            )
            
        except Exception as e:
            logger.error("Patch application failed", error=str(e))
            return OperationResult(
                operation=CodexOperation.PATCH,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None,
        server_name: Optional[str] = None
    ) -> OperationResult:
        """Call an MCP tool"""
        
        start_time = time.time()
        
        try:
            if not self._initialized:
                await self.initialize()
            
            # Get session
            session = self.get_session(session_id) if session_id else None
            
            # Check tool permissions
            if not self.mcp_client.tool_registry.is_tool_allowed(tool_name):
                return OperationResult(
                    operation=CodexOperation.TOOL_CALL,
                    success=False,
                    error=f"Tool not allowed: {tool_name}",
                    execution_time=time.time() - start_time
                )
            
            # Call tool
            result = await self.mcp_client.call_tool(tool_name, arguments, server_name)
            
            # Record tool usage
            self.mcp_client.tool_registry.record_tool_usage(tool_name)
            
            return OperationResult(
                operation=CodexOperation.TOOL_CALL,
                success=True,
                result=result,
                execution_time=time.time() - start_time,
                metadata={
                    "tool_name": tool_name,
                    "server_name": server_name
                }
            )
            
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            return OperationResult(
                operation=CodexOperation.TOOL_CALL,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _build_system_context(self, working_directory: str, session: Optional[CodexSession]) -> str:
        """Build system context for LLM"""
        
        context_parts = [
            "You are Codex, an AI programming assistant.",
            f"Current working directory: {working_directory}",
        ]
        
        if session:
            context_parts.append(f"Session ID: {session.id}")
            if session.user:
                context_parts.append(f"User: {session.user}")
        
        # Add available tools context
        if self._initialized:
            tools = self.mcp_client.tool_registry.list_tools()
            if tools:
                context_parts.append(f"\nAvailable tools ({len(tools)}):")
                for tool in tools[:10]:  # Show first 10 tools
                    context_parts.append(f"- {tool.name}: {tool.description}")
                if len(tools) > 10:
                    context_parts.append(f"... and {len(tools) - 10} more tools")
        
        context_parts.append("\nYou can help with:")
        context_parts.append("- Code analysis and generation")
        context_parts.append("- File operations and search")
        context_parts.append("- Command execution (with approval)")
        context_parts.append("- Patch application")
        context_parts.append("- Using available tools")
        
        # Embed AGENTS.md or similar project doc (max ~32 KiB)
        for name in ["AGENTS.md", "agents.md", "README_CODING.md"]:
            p = Path(working_directory) / name
            if p.exists():
                try:
                    data = p.read_bytes()[:32 * 1024]
                    context_parts.append("\nProject instructions (truncated):\n" + data.decode("utf-8", errors="replace"))
                except Exception:
                    pass
                break

        return "\n".join(context_parts)
    
    async def _get_available_tools(self, session_id: Optional[str] = None) -> List[LLMTool]:
        """Get available tools as LLM tools"""
        
        if not self._initialized:
            await self.initialize()
        
        tools = []
        # Built-in tools: exec and apply_patch and file_search
        tools.append(LLMTool(
            name="local_shell",
            description="Execute a shell command in a sandboxed environment (may require approval)",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "array", "items": {"type": "string"}},
                    "cwd": {"type": "string"},
                    "env": {"type": "object"}
                },
                "required": ["command"]
            }
        ))
        tools.append(LLMTool(
            name="exec_start",
            description="Start a persistent exec session (interactive process)",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "array", "items": {"type": "string"}},
                    "cwd": {"type": "string"},
                    "env": {"type": "object"}
                },
                "required": ["command"]
            }
        ))
        tools.append(LLMTool(
            name="write_stdin",
            description="Write data to a persistent exec session's stdin",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "data": {"type": "string"}
                },
                "required": ["session_id", "data"]
            }
        ))
        tools.append(LLMTool(
            name="exec_stop",
            description="Stop a persistent exec session",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ))
        tools.append(LLMTool(
            name="apply_patch",
            description="Apply a unified diff patch to the workspace (approval may be required)",
            parameters={
                "type": "object",
                "properties": {"patch": {"type": "string"}, "root": {"type": "string"}},
                "required": ["patch"]
            }
        ))
        tools.append(LLMTool(
            name="file_search",
            description="Search files in the workspace by fuzzy/regex/glob",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "mode": {"type": "string", "enum": ["fuzzy", "exact", "regex", "glob"]},
                    "root": {"type": "string"}
                },
                "required": ["pattern"]
            }
        ))
        tools.append(LLMTool(
            name="update_plan",
            description="Update the current execution plan and step statuses",
            parameters={
                "type": "object",
                "properties": {
                    "steps": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["steps"]
            }
        ))
        mcp_tools = self.mcp_client.tool_registry.list_tools()
        
        for tool_info in mcp_tools:
            llm_tool = LLMTool(
                name=tool_info.name,
                description=tool_info.description,
                parameters=tool_info.input_schema
            )
            tools.append(llm_tool)
        
        return tools
    
    async def get_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive status information"""
        
        status = {
            "orchestrator": {
                "initialized": self._initialized,
                "active_sessions": len(self.sessions),
                "operation_history": len(self.operation_history)
            },
            "llm": {
                "clients": list(self.llm_manager.clients.keys()),
                "default_client": self.llm_manager.default_client
            },
            "mcp": await self.mcp_client.health_check() if self._initialized else {"status": "not_initialized"},
            "search": self.search_manager.get_stats(),
            "approval": self.approval_manager.get_approval_stats(),
            "policy": self.policy_manager.get_stats()
        }
        
        # Add session-specific info
        if session_id:
            session = self.get_session(session_id)
            if session:
                status["session"] = {
                    "id": session.id,
                    "user": session.user,
                    "working_directory": session.working_directory,
                    "created_at": session.created_at,
                    "last_activity": session.last_activity
                }
        
        return status
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        logger.info("Cleaning up Codex orchestrator")
        
        # Close all sessions
        for session_id in list(self.sessions.keys()):
            self.close_session(session_id)
        
        # Close LLM clients
        await self.llm_manager.close_all()
        
        # Close MCP client
        await self.mcp_client.close()
        
        # Clean up managers
        await self.search_manager.close()
        # approval cleanup is synchronous and returns an int
        try:
            self.approval_manager.cleanup_expired_requests()
        except Exception:
            pass
        
        self._initialized = False
        # Stop local mux
        try:
            if hasattr(self, '_exec_mux') and self._exec_mux:
                await self._exec_mux.stop()
                self._exec_mux = None
        except Exception:
            pass
        logger.info("Codex orchestrator cleaned up")

    async def execute_builtin_tool(self, name: str, arguments: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a built-in tool by name and return a structured result."""
        if name == "local_shell":
            cmd = arguments.get("command")
            if not isinstance(cmd, list) or not all(isinstance(x, str) for x in cmd):
                raise ValueError("local_shell.command must be a list of strings")
            res = await self.execute_command(cmd, session_id=session_id, cwd=arguments.get("cwd"), env=arguments.get("env"))
            return {
                "success": res.success,
                "exit_code": res.result.get("returncode"),
                "stdout": res.result.get("stdout"),
                "stderr": res.result.get("stderr"),
            }
        if name == "apply_patch":
            patch_text = arguments.get("patch")
            if not isinstance(patch_text, str) or not patch_text:
                raise ValueError("apply_patch.patch must be a non-empty string")
            res = await self.apply_patch(patch_text, session_id=session_id, root_path=arguments.get("root"))
            return {"success": res.success, "details": res.metadata}
        if name == "file_search":
            pattern = arguments.get("pattern")
            if not isinstance(pattern, str) or not pattern:
                raise ValueError("file_search.pattern is required")
            mode = arguments.get("mode")
            root = arguments.get("root")
            res = await self.search_files(pattern, session_id=session_id, root_path=root, mode=mode)
            return {"success": res.success, "files": [r.path for r in (res.result or [])]}
        if name == "update_plan":
            steps = arguments.get("steps")
            if not isinstance(steps, list):
                raise ValueError("update_plan.steps must be a list of step dicts")
            self.shared_plan = steps
            return {"success": True, "plan": self.shared_plan}
        if name == "exec_start":
            # start persistent exec session
            cmd = arguments.get("command") or []
            if not isinstance(cmd, list) or not all(isinstance(x, str) for x in cmd):
                raise ValueError("exec_start.command must be a list of strings")
            # publish exec session output to event bus
            def _on_output(stream: str, data: bytes):
                try:
                    import base64
                    b64 = base64.b64encode(data).decode('ascii')
                    asyncio.create_task(self.events.publish(
                        "exec_session_output",
                        session_id=session_id or "",
                        stream=stream,
                        data_b64=b64,
                    ))
                except Exception:
                    pass

            sid = await self._exec_sessions.start_session(
                cmd,
                session_id=session_id,
                cwd=arguments.get("cwd"),
                env=arguments.get("env"),
                on_output=_on_output,
            )
            # notify bus
            try:
                await self.events.publish("exec_session_started", session_id=sid)
            except Exception:
                pass
            return {"success": True, "session_id": sid}
        if name == "write_stdin":
            sid = arguments.get("session_id")
            data = arguments.get("data")
            if not sid or not isinstance(data, str):
                raise ValueError("write_stdin requires session_id and text data")
            await self._exec_sessions.write_stdin(sid, data)
            return {"success": True}
        if name == "exec_stop":
            sid = arguments.get("session_id")
            if not sid:
                raise ValueError("exec_stop requires session_id")
            await self._exec_sessions.stop_session(sid)
            try:
                await self.events.publish("exec_session_stopped", session_id=sid)
            except Exception:
                pass
            return {"success": True}
        raise ValueError(f"Unknown built-in tool: {name}")

    # removed old snapshot/diff helpers; using turn_diff_tracker now
