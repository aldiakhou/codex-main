"""
Cadenza CLI - Model Context Protocol client/orchestrator
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
import structlog

from .core.client import CodexClient
from .core.config import Config
from .proto.events_adapter import EventsAdapter
from .auth.store import save_api_key, load_api_key, clear_auth, safe_format_key


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def _should_color(ctx) -> bool:
    mode = (ctx.obj or {}).get("color_mode", "auto")
    if mode == "always":
        return True
    if mode == "never":
        return False
    # auto
    try:
        import os, sys
        if os.getenv("NO_COLOR"):
            return False
        return sys.stdout.isatty()
    except Exception:
        return False


@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
@click.option("--override", "-o", multiple=True, help="Override config key=value (supports dotted paths)")
@click.option("--log-level", default="INFO", help="Log level (DEBUG, INFO, WARNING, ERROR)")
@click.option(
    "--sandbox",
    type=click.Choice(["read-only", "workspace-write", "danger-full-access"], case_sensitive=False),
    help="Select sandbox policy (overrides config)",
)
@click.option(
    "--color",
    type=click.Choice(["always", "never", "auto"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Color settings for CLI output",
)
@click.pass_context
def cli(ctx, config, override, log_level, sandbox, color):
    """Cadenza - Model Context Protocol Client"""
    ctx.ensure_object(dict)
    
    # Set log level
    import logging
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    def _deep_set(d: dict, path: str, value):
        keys = path.split('.')
        cur = d
        for k in keys[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                cur[k] = {}
            cur = cur[k]
        cur[keys[-1]] = value

    def _apply_overrides(cfg_obj: Config, overrides: tuple[str, ...]) -> Config:
        if not overrides:
            return cfg_obj
        base = cfg_obj.to_dict()
        import json as _json
        for item in overrides:
            if '=' not in item:
                continue
            k, v = item.split('=', 1)
            try:
                # try to parse JSON value
                parsed = _json.loads(v)
            except Exception:
                parsed = v
            _deep_set(base, k, parsed)
        return Config.from_dict(base)

    # Load configuration
    if config:
        cfg = Config.from_file(config)
        cfg2 = _apply_overrides(cfg, override)
    else:
        # Try to load from default locations
        default_paths = [
            "codex.json",
            "codex-config.json",
            Path.home() / ".codex" / "config.json",
        ]

        config_obj = None
        for path in default_paths:
            if Path(path).exists():
                try:
                    config_obj = Config.from_file(path)
                    break
                except Exception as e:
                    logger.warning("Failed to load config file", path=path, error=str(e))

        if config_obj is None:
            # Fall back to environment variables
            config_obj = Config.from_env()

        cfg2 = _apply_overrides(config_obj, override)

    if sandbox:
        # Map CLI sandbox flag to config
        cfg2.enable_sandbox = sandbox.lower() != "danger-full-access"
        cfg2.sandbox_mode = {
            "read-only": "read-only",
            "workspace-write": "workspace",
            "danger-full-access": "danger-full-access",
        }[sandbox.lower()]

    ctx.obj["config"] = cfg2
    ctx.obj["color_mode"] = (color or "auto").lower()
    # Apply color env hints for click and downstream tools
    try:
        import os
        cm = ctx.obj["color_mode"]
        if cm == "never":
            os.environ["NO_COLOR"] = "1"
            os.environ["CLICOLOR"] = "0"
        elif cm == "always":
            os.environ["CLICOLOR_FORCE"] = "1"
            os.environ["CLICOLOR"] = "1"
    except Exception:
        pass


@cli.command()
@click.pass_context
def list_servers(ctx):
    """List configured servers"""
    config = ctx.obj["config"]
    
    if not config.servers:
        click.echo("No servers configured.")
        return
    
    click.echo("Configured servers:")
    for name, server in config.servers.items():
        status = "configured"
        click.echo(f"  {name}: {server.transport} - {status}")


@cli.command()
@click.option("--api-key", envvar="OPENAI_API_KEY", help="API key to store (or use env OPENAI_API_KEY)")
def login(api_key: Optional[str]):
    """Login by storing an API key under ~/.codex/auth.json."""
    if not api_key:
        api_key = click.prompt("Enter API key", hide_input=True)
    try:
        save_api_key(api_key)
        click.echo("Successfully logged in")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command(name="login-status")
def login_status_cmd():
    """Show login status."""
    key = load_api_key()
    if key:
        click.echo(f"Logged in with API key - {safe_format_key(key)}")
    else:
        click.echo("Not logged in")


@cli.command()
def logout():
    """Logout by removing stored credentials."""
    try:
        removed = clear_auth()
        if removed:
            click.echo("Successfully logged out")
        else:
            click.echo("Not logged in")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.option("--server", "-s", help="Specific server to query")
@click.pass_context
async def list_tools(ctx, server):
    """List available tools"""
    config = ctx.obj["config"]
    
    async with CodexClient(config) as client:
        try:
            # Prefer registry (qualified names)
            tools_info = client.tool_registry.list_tools(server_name=server)
            if not tools_info:
                click.echo("No tools available.")
                return
            
            click.echo(f"Available tools ({len(tools_info)}):")
            for info in tools_info:
                name = client.tool_registry.qualified_name_for(info) or info.name
                click.echo(f"  {name}: {info.description}")
                
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.argument("cmd", nargs=-1, required=True)
@click.option("--cwd", type=click.Path(), help="Working directory")
@click.option("--env", multiple=True, help="Environment VAR=VALUE (repeat)")
@click.pass_context
async def exec(ctx, cmd, cwd, env):
    """Execute a command via MCP exec tool (approval by default)."""
    config = ctx.obj["config"]
    env_dict = {}
    for kv in env:
        if "=" in kv:
            k, v = kv.split("=", 1)
            env_dict[k] = v
    # Prefer MCP; fallback to orchestrator
    try:
        async with CodexClient(config) as client:
            args = {
                "command": list(cmd),
                "cwd": cwd,
                "env": env_dict,
                "stream": False,
                "requireApproval": True,
            }
            result = await client.call_tool("exec", args)
            sc = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
            if sc:
                rc = int(sc.get("returncode") or 0)
                out = sc.get("stdout") or ""
                err = sc.get("stderr") or ""
                if out:
                    click.echo(out, nl=False)
                if rc != 0 and err:
                    click.echo(err, err=True)
                sys.exit(0 if rc == 0 else 1)
            # Fallback to text block
            from mcp.types import TextContent  # type: ignore
            txts = [c for c in (result.content or []) if isinstance(c, TextContent)]
            if txts:
                click.echo(txts[0].text or "", nl=False)
            sys.exit(0)
    except Exception:
        from .core.orchestrator import CodexOrchestrator
        orch = CodexOrchestrator(config)
        await orch.initialize()
        try:
            res = await orch.execute_command(list(cmd), cwd=cwd, env=env_dict)
            click.echo(res.result.get("stdout", ""), nl=False)
            if res.result.get("stderr"):
                click.echo(res.result["stderr"], err=True)
            sys.exit(0 if res.success else 1)
        finally:
            await orch.cleanup()


@cli.command(name="exec-stream")
@click.argument("cmd", nargs=-1, required=True)
@click.option("--cwd", type=click.Path(), help="Working directory")
@click.option("--env", multiple=True, help="Environment VAR=VALUE (repeat)")
@click.option("--interval", type=float, default=0.25, help="Poll interval when using MCP pull stream")
@click.pass_context
async def exec_stream(ctx, cmd, cwd, env, interval):
    """Stream command output live via MCP notifications (preferred) or polling fallback; else local streaming."""
    config = ctx.obj["config"]
    env_dict = {}
    for kv in env:
        if "=" in kv:
            k, v = kv.split("=", 1)
            env_dict[k] = v
    try:
        async with CodexClient(config) as client:
            # Start streaming exec on server
            args = {
                "command": list(cmd),
                "cwd": cwd,
                "env": env_dict,
                "stream": True,
                "requireApproval": True,
            }
            result = await client.call_tool("exec", args)
            sc = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
            req_id = sc.get("request_id") if sc else None
            if not req_id:
                raise RuntimeError("failed to start exec stream")
            # Try notifications/progress first
            async def try_push(timeout: float = 1.0) -> bool:
                try:
                    first = True
                    async for ev in client.progress_events(kinds=["codex.exec.delta", "codex.exec.completed"]):
                        if first:
                            # Allow a short warm-up window for availability
                            first = False
                        kind = ev.get("kind") or ev.get("type")
                        if ev.get("request_id") != req_id:
                            continue
                        if kind == "codex.exec.delta":
                            import base64
                            data_b64 = ev.get("data_b64") or ""
                            try:
                                b = base64.b64decode(data_b64)
                            except Exception:
                                b = b""
                            if (ev.get("stream") or "stdout") == "stderr":
                                click.echo(b.decode("utf-8", errors="ignore"), nl=False, err=True)
                            else:
                                click.echo(b.decode("utf-8", errors="ignore"), nl=False)
                        elif kind == "codex.exec.completed":
                            rc = ev.get("returncode")
                            sys.exit(0 if (rc is None or int(rc) == 0) else 1)
                    return False
                except Exception:
                    return False

            used_push = await try_push()
            if not used_push:
                # Fallback to polling
                import base64
                while True:
                    polled = await client.call_tool("codex-exec-poll", {"request_id": req_id, "max_chunks": 100})
                    sc2 = getattr(polled, "structured_content", None) or getattr(polled, "structuredContent", None)
                    for ch in sc2.get("chunks", []) or []:
                        data_b64 = ch.get("data_b64") or ""
                        stream = ch.get("stream") or "stdout"
                        try:
                            b = base64.b64decode(data_b64)
                        except Exception:
                            b = b""
                        if stream == "stderr":
                            try:
                                click.echo(b.decode("utf-8", errors="ignore"), nl=False, err=True)
                            except Exception:
                                pass
                        else:
                            try:
                                click.echo(b.decode("utf-8", errors="ignore"), nl=False)
                            except Exception:
                                pass
                    if sc2.get("completed"):
                        rc = sc2.get("returncode")
                        sys.exit(0 if (rc is None or int(rc) == 0) else 1)
                    await asyncio.sleep(interval)
    except Exception:
        # Fallback: local orchestrator streaming
        from .core.orchestrator import CodexOrchestrator
        orch = CodexOrchestrator(config)
        await orch.initialize()
        try:
            async for item in orch.execute_command_stream(list(cmd), cwd=cwd, env=env_dict):
                if item.get("type") == "delta":
                    if item.get("stream") == "stdout":
                        click.echo(item.get("data", b"").decode(errors="ignore"), nl=False)
                    else:
                        click.echo(item.get("data", b"").decode(errors="ignore"), nl=False, err=True)
                elif item.get("type") == "error":
                    click.echo(f"Error: {item['message']}", err=True)
                    sys.exit(1)
                elif item.get("type") == "result":
                    sys.exit(0 if item.get("returncode", 1) == 0 else 1)
        finally:
            await orch.cleanup()


@cli.command(name="agent-exec")
@click.argument("prompt", required=False)
@click.option("--json", "json_mode", is_flag=True, help="Emit JSONL events instead of human output")
@click.option("--cwd", type=click.Path(), help="Working directory for the session")
@click.option("--session-id", type=str, help="Optional session id (default: auto)")
@click.option("--image", "images", multiple=True, type=click.Path(exists=True), help="Attach image(s) to the initial prompt (multi-modal)")
@click.option("--output-last-message", type=click.Path(), help="Write final assistant message to file")
@click.pass_context
async def agent_exec(ctx, prompt: Optional[str], json_mode: bool, cwd: Optional[str], session_id: Optional[str], images: tuple[str, ...], output_last_message: Optional[str]):
    """Run an agent loop against a PROMPT using the Orchestrator.

    Streams assistant deltas and basic tool notifications; prints final result.
    """
    config = ctx.obj["config"]

    # Read prompt from stdin if not provided or set to '-'
    if not prompt or prompt == "-":
        try:
            data = sys.stdin.read()
            prompt = data.strip()
        except Exception:
            prompt = ""
    if not prompt:
        click.echo("No prompt provided. Pass PROMPT or pipe to stdin.", err=True)
        raise SystemExit(1)

    from .core.orchestrator import CodexOrchestrator
    orch = CodexOrchestrator(config)
    await orch.initialize()

    # Session setup
    import uuid
    sid = session_id or str(uuid.uuid4())
    workdir = cwd or str(Path.cwd())
    orch.create_session(sid, workdir)

    # Turn/event id to correlate substreams
    import uuid as _uuid
    turn_id = str(_uuid.uuid4())
    adapter = EventsAdapter(json_mode=json_mode, event_id=turn_id, originator="cadenza_cli_py", session_id=sid, session_cwd=workdir)

    async def consume_event_bus():
        # Forward a subset of orchestrator events
        async for ev in orch.events.subscribe(types=[
            "tool_start", "tool_end", "exec_begin", "exec_end", "patch_begin", "patch_end", "approval_request", "turn_diff", "exec_session_output"
        ]):
            out = adapter.from_bus_event(ev)
            if out is not None:
                _emit(out, json_mode)

    # Emit a minimal SessionConfigured + TaskStarted
    _emit(adapter.session_configured(sid, workdir), json_mode)
    _emit(adapter.task_started(sid, prompt), json_mode)

    # Start background consumer
    bus_task = asyncio.create_task(consume_event_bus())

    last_len = 0
    final_text: Optional[str] = None
    try:
        # Drive the chat loop with streaming (attach images if any)
        initial_msg = {"role": "user", "content": prompt}
        if images:
            initial_msg["images"] = list(images)
        async for item in orch.chat([initial_msg], session_id=sid, stream=True):
            # Stream deltas
            if isinstance(item, dict) and item.get("type") == "delta":
                content = item.get("content") or ""
                # compute only the new suffix
                new = content[last_len:]
                last_len = len(content)
                if new:
                    _emit(adapter.agent_message_delta(new), json_mode)
                continue

            # Reasoning deltas (if available from provider)
            if isinstance(item, dict) and item.get("type") == "reasoning_raw_delta":
                _emit(adapter.reasoning_raw_delta(item.get("content") or ""), json_mode)
                continue
            if isinstance(item, dict) and item.get("type") == "reasoning_delta":
                _emit(adapter.reasoning_delta(item.get("content") or ""), json_mode)
                continue
            # Tool result surfaced from provider
            if isinstance(item, dict) and item.get("type") == "tool_result":
                _emit(adapter.tool_result(item.get("name"), item.get("content") or ""), json_mode)
                continue

            # Tool lifecycle notifications from the chat loop
            if isinstance(item, dict) and item.get("type") in ("tool_start", "tool_end"):
                name = item.get("name") or "unknown"
                if item.get("type") == "tool_start":
                    # Reasoning section break around tool calls
                    _emit(adapter.reasoning_section_break("tool"), json_mode)
                    _emit(adapter.tool_call_begin(name), json_mode)
                else:
                    _emit(adapter.tool_call_end(name, success=True), json_mode)
                continue

            # Non-stream snapshots or completion
            if isinstance(item, dict) and "content" in item and item.get("tool_calls") == []:
                final_text = item.get("content")
                if final_text:
                    _emit(adapter.agent_message(final_text), json_mode)
                break
    finally:
        bus_task.cancel()
        try:
            await orch.cleanup()
        except Exception:
            pass

    if final_text is None:
        final_text = ""

    _emit(adapter.task_complete(final_text), json_mode)
    # Write last message to file if requested
    if output_last_message:
        try:
            Path(output_last_message).write_text(final_text, encoding="utf-8")
        except Exception:
            pass


def _emit(event: dict, json_mode: bool) -> None:
    if json_mode:
        click.echo(json.dumps(event, ensure_ascii=False))
    else:
        # Minimal human formatting
        t = event.get("type")
        if t == "agent_message_delta":
            click.echo(event.get("content", ""), nl=False)
        elif t == "tool_call_begin":
            click.echo(f"\n→ tool: {event.get('name')}")
        elif t == "tool_result":
            content = event.get("content") or ""
            if content:
                click.echo("\n" + content)
        elif t == "tool_call_end":
            click.echo(f"✓ tool done: {event.get('name')}")
        elif t == "ToolResult":
            content = event.get("content") or ""
            if content:
                click.echo("\n" + content)
        elif t == "ExecSessionOutput":
            # Human mode: decode base64 for display
            import base64
            b64 = event.get("data_b64") or ""
            try:
                chunk = base64.b64decode(b64)
                try:
                    click.echo(chunk.decode('utf-8'), nl=False)
                except Exception:
                    # If not valid UTF-8, print as latin-1 fallback
                    click.echo(chunk.decode('latin-1', errors='replace'), nl=False)
            except Exception:
                pass
        elif t == "task_complete":
            click.echo("\n\n---\n" + (event.get("final_text") or ""))


@cli.command(name="exec-stdin")
@click.option("--session-id", required=True, help="Persistent exec session id")
@click.option("--data", help="Data to write (default: read from stdin)")
@click.pass_context
async def exec_stdin(ctx, session_id: str, data: Optional[str]):
    """Write to stdin of a persistent exec session (same-process only)."""
    config = ctx.obj["config"]
    from .core.orchestrator import CodexOrchestrator
    orch = CodexOrchestrator(config)
    await orch.initialize()
    try:
        if data is None:
            data = sys.stdin.read()
        res = await orch.execute_builtin_tool("write_stdin", {"session_id": session_id, "data": data})
        if not res.get("success"):
            click.echo("Failed to write to stdin", err=True)
            sys.exit(1)
    finally:
        await orch.cleanup()


@cli.command(name="exec-stdin-remote")
@click.option("--session-id", required=True, help="Persistent exec session id")
@click.option("--data", help="Data to write (default: read from stdin)")
def exec_stdin_remote(session_id: str, data: Optional[str]):
    """Write to stdin of a persistent exec session via local mux (cross-process)."""
    try:
        if data is None:
            data = sys.stdin.read()
        import json as _json
        import socket, base64
        # Read mux port
        from .auth.store import codex_home_dir
        p = codex_home_dir() / "execmux.json"
        cfg = _json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
        port = int(cfg.get('port', 0))
        token = cfg.get('token')
        if port <= 0:
            click.echo("Exec mux not running.", err=True)
            sys.exit(1)
        req = {
            "op": "write_stdin",
            "session_id": session_id,
            "data_b64": base64.b64encode((data or "").encode('utf-8')).decode('ascii'),
            "token": token,
        }
        with socket.create_connection(("127.0.0.1", port), timeout=3.0) as s:
            s.sendall(_json.dumps(req).encode('utf-8'))
            s.shutdown(socket.SHUT_WR)
            resp = s.recv(65536)
        out = _json.loads(resp.decode('utf-8'))
        if not out.get("ok"):
            click.echo(f"Error: {out.get('error')}", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command(name="apply-patch")
@click.option("--file", "patch_file", type=click.Path(exists=True), help="Patch file path (defaults to stdin)")
@click.option("--root", "root_path", type=click.Path(), help="Patch root path")
@click.pass_context
async def apply_patch_cmd(ctx, patch_file, root_path):
    """Apply a unified diff patch via MCP (reads stdin if --file not given)."""
    config = ctx.obj["config"]
    patch_text = Path(patch_file).read_text(encoding="utf-8") if patch_file else sys.stdin.read()
    try:
        async with CodexClient(config) as client:
            args = {"patch": patch_text, "root": root_path, "requireApproval": True}
            result = await client.call_tool("apply_patch", args)
            sc = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
            ok = bool(sc.get("success")) if sc else True
            if ok:
                click.echo("Patch applied successfully")
                sys.exit(0)
            else:
                click.echo("Patch failed", err=True)
                sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pattern", required=True)
@click.option("--mode", type=click.Choice(["fuzzy", "exact", "regex", "glob"]), default="fuzzy")
@click.option("--root", type=click.Path(), help="Search root path")
@click.pass_context
async def search(ctx, pattern, mode, root):
    """Search files in workspace."""
    config = ctx.obj["config"]
    from .core.orchestrator import CodexOrchestrator
    orch = CodexOrchestrator(config)
    await orch.initialize()
    try:
        res = await orch.search_files(pattern, root_path=root, **{"mode": mode})
        if res.success:
            for r in res.result:
                click.echo(r.path)
            sys.exit(0)
        else:
            click.echo(f"Search failed: {res.error}")
            sys.exit(1)
    finally:
        await orch.cleanup()


@cli.command()
@click.argument("tool_name")
@click.argument("arguments", nargs=-1)
@click.option("--server", "-s", help="Server to use")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
async def call_tool(ctx, tool_name, arguments, server, output_json):
    """Call a tool with arguments"""
    config = ctx.obj["config"]
    
    # Parse arguments
    args_dict = {}
    for arg in arguments:
        if "=" in arg:
            key, value = arg.split("=", 1)
            # Try to parse as JSON, fall back to string
            try:
                args_dict[key] = json.loads(value)
            except json.JSONDecodeError:
                args_dict[key] = value
    
    async with CodexClient(config) as client:
        try:
            result = await client.call_tool(tool_name, args_dict, server)
            
            if output_json:
                # Output as JSON
                output = {
                    "tool": tool_name,
                    "server": server,
                    "arguments": args_dict,
                    "result": [
                        {
                            "type": content.type,
                            "text": content.text if hasattr(content, "text") else None,
                            "data": content.data if hasattr(content, "data") else None,
                            "mimeType": content.mimeType if hasattr(content, "mimeType") else None,
                        }
                        for content in result.content
                    ]
                }
                click.echo(json.dumps(output, indent=2))
            else:
                # Output as text
                for content in result.content:
                    if hasattr(content, "text") and content.text:
                        click.echo(content.text)
                    elif hasattr(content, "data"):
                        click.echo(f"[Binary data: {len(content.data)} bytes]")
                    else:
                        click.echo(f"[Content type: {content.type}]")
                        
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.option("--server", "-s", help="Specific server to check")
@click.pass_context
async def health(ctx, server):
    """Check server health"""
    config = ctx.obj["config"]
    
    async with CodexClient(config) as client:
        try:
            if server:
                info = await client.get_server_info(server)
                click.echo(f"Server: {server}")
                click.echo(f"Status: {'Connected' if info.get('connected') else 'Disconnected'}")
                if info.get('error'):
                    click.echo(f"Error: {info['error']}")
                if info.get('tool_count'):
                    click.echo(f"Tools: {info['tool_count']}")
            else:
                health_info = await client.health_check()
                click.echo(f"Overall Status: {health_info['status']}")
                click.echo(f"Healthy Servers: {health_info['healthy_servers']}/{health_info['total_servers']}")
                
                for server_name, status in health_info['servers'].items():
                    click.echo(f"  {server_name}: {status['status']}")
                    if status.get('error'):
                        click.echo(f"    Error: {status['error']}")
                        
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="table", help="Output format")
@click.pass_context
async def status(ctx, output_format):
    """Show detailed status information"""
    config = ctx.obj["config"]
    
    async with CodexClient(config) as client:
        try:
            servers_info = await client.get_all_servers_info()
            health_info = await client.health_check()
            
            if output_format == "json":
                output = {
                    "health": health_info,
                    "servers": servers_info
                }
                click.echo(json.dumps(output, indent=2))
            else:
                click.echo("=== Codex Status ===")
                click.echo(f"Overall Status: {health_info['status']}")
                click.echo(f"Healthy Servers: {health_info['healthy_servers']}/{health_info['total_servers']}")
                click.echo()
                
                for server_name, info in servers_info.items():
                    click.echo(f"Server: {server_name}")
                    click.echo(f"  Status: {'Connected' if info.get('connected') else 'Disconnected'}")
                    if info.get('tool_count'):
                        click.echo(f"  Tools: {info['tool_count']}")
                        if info.get('tools'):
                            click.echo(f"  Tool Names: {', '.join(info['tools'][:5])}{'...' if len(info['tools']) > 5 else ''}")
                    if info.get('error'):
                        click.echo(f"  Error: {info['error']}")
                    click.echo()
                    
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.option("--n", default=100, type=int, help="Number of history events")
@click.pass_context
async def history(ctx, n):
    """Show recent history events."""
    try:
        from .utils.history import tail
        from .core.config import Config
        cfg: Config = ctx.obj["config"]
        events = tail(n=n, path=getattr(cfg, "history_path", None))
        for e in events:
            click.echo(json.dumps(e))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--types", multiple=True, help="Event types to include (repeat)")
@click.pass_context
async def events(ctx, types):
    """Subscribe to in-proc event bus and print events."""
    config = ctx.obj["config"]
    from .core.orchestrator import CodexOrchestrator
    orch = CodexOrchestrator(config)
    await orch.initialize()
    try:
        click.echo("Subscribing to events... (Ctrl+C to stop)")
        async for ev in orch.events.subscribe(types=list(types) or None):
            click.echo(json.dumps(ev))
    except KeyboardInterrupt:
        pass
    finally:
        await orch.cleanup()


@cli.command()
@click.argument("output_file", type=click.Path())
@click.pass_context
async def export_config(ctx, output_file):
    """Export configuration to file"""
    config = ctx.obj["config"]
    
    output_path = Path(output_file)
    
    try:
        with open(output_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        click.echo(f"Configuration exported to {output_path}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("prompt", nargs=-1, required=True)
@click.option("--image", "images", multiple=True, type=click.Path(exists=True), help="Attach image(s) to the initial prompt")
@click.option("--output-last-message", type=click.Path(), help="Write final assistant message to file")
@click.option("--stream/--no-stream", default=True, help="Stream responses")
@click.pass_context
async def chat(ctx, prompt, images, output_last_message, stream):
    """Chat with LLM (uses built-in tool loop)."""
    config = ctx.obj["config"]
    from .core.orchestrator import CodexOrchestrator
    orch = CodexOrchestrator(config)
    await orch.initialize()
    try:
        text = " ".join(prompt)
        msg = {"role": "user", "content": text}
        if images:
            msg["images"] = list(images)
        gen = orch.chat([msg], stream=stream)

        if stream:
            printed = 0
            async for item in gen:
                if not isinstance(item, dict):
                    continue
                itype = item.get("type")
                if itype == "delta":
                    s = item.get("content", "") or ""
                    if s and len(s) >= printed:
                        suffix = s[printed:]
                        printed = len(s)
                        if suffix:
                            click.secho(suffix, fg="cyan", nl=False)
                elif itype == "tool_start":
                    name = item.get("name", "tool")
                    click.secho(f"\n[tool ▶] {name}\n", fg="yellow")
                elif itype == "tool_end":
                    name = item.get("name", "tool")
                    click.secho(f"[tool ✓] {name}\n", fg="yellow")
                # ignore other snapshots during streaming
            click.echo()
        else:
            final = None
            async for item in gen:
                if isinstance(item, dict):
                    content = item.get("content")
                    if content:
                        final = content
            if final:
                click.secho(final, fg="green")
            if output_last_message and final:
                try:
                    Path(output_last_message).write_text(final, encoding="utf-8")
                except Exception:
                    pass
    finally:
        await orch.cleanup()


@cli.command()
@click.option("--host", default="[::]", help="gRPC host to bind to (use [::] for IPv4/IPv6)")
@click.option("--port", default=50051, type=int, help="gRPC port to bind to")
@click.pass_context
async def serve(ctx, host, port):
    """Start Cadenza gRPC server (CodexService)."""
    config = ctx.obj["config"]
    from .core.client import CodexClient
    from .core.orchestrator import CodexOrchestrator
    from .proto.grpc_service import CodexGRPCServer

    client = CodexClient(config)
    orch = CodexOrchestrator(config)
    server = CodexGRPCServer(client, host=host, port=port, orchestrator=orch)

    click.echo(f"Starting Cadenza gRPC on {host}:{port} (Ctrl+C to stop)")
    try:
        await server.start()
        await server.wait_for_termination()
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
    finally:
        await server.stop(0.5)


@cli.command(name="mcp")
@click.pass_context
async def mcp_server(ctx):
    """Run the MCP server over stdio (tools: codex, codex-reply)."""
    config = ctx.obj["config"]
    from .mcp.server import CodexMCPServer

    srv = CodexMCPServer(config)
    try:
        await srv.run_stdio()
    except KeyboardInterrupt:
        pass


@cli.command(name="proto")
@click.argument("prompt", required=False)
@click.option("--cwd", type=click.Path(), help="Working directory for the session")
@click.option("--stdin", "stdin_mode", is_flag=True, help="Read protocol submissions from stdin (JSONL)")
@click.pass_context
async def proto(ctx, prompt: Optional[str], cwd: Optional[str], stdin_mode: bool):
    """Run protocol stream: emit codex-protocol events to stdout as JSONL.

    If --stdin is used, reads submissions from stdin. Otherwise uses PROMPT or reads a single prompt from stdin.
    """
    config = ctx.obj["config"]
    if stdin_mode:
        from .protocol.stream import run_protocol_stdin
        await run_protocol_stdin(config, cwd=cwd)
        return
    if not prompt:
        try:
            data = sys.stdin.read()
            prompt = (data or "").strip()
        except Exception:
            prompt = ""
    if not prompt:
        click.echo("No prompt provided. Pass PROMPT or pipe to stdin.", err=True)
        raise SystemExit(1)

    from .protocol.stream import run_protocol_stream
    await run_protocol_stream(prompt, config, cwd=cwd)


@cli.command(name="respond-approval")
@click.argument("request_id", required=True)
@click.argument("decision", required=True, type=click.Choice(["approved", "denied", "cancelled"], case_sensitive=False))
@click.option("--responder", type=str, default=None, help="Responder identifier")
@click.option("--reason", type=str, default=None, help="Optional reason")
@click.pass_context
async def respond_approval(ctx, request_id: str, decision: str, responder: Optional[str], reason: Optional[str]):
    """Respond to a pending approval via MCP."""
    config = ctx.obj["config"]
    async with CodexClient(config) as client:
        args = {"request_id": request_id, "decision": decision.lower(), "responder": responder, "reason": reason}
        result = await client.call_tool("codex-respond-approval", args)
        sc = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
        ok = bool(sc.get("updated")) if sc else True
        click.echo("OK" if ok else "Not updated")


@cli.command(name="watch-approvals")
@click.option("--session-id", help="Filter approvals by session id")
@click.option("--interval", type=float, default=2.0, help="Polling interval seconds (if server watch unavailable)")
@click.pass_context
async def watch_approvals(ctx, session_id: Optional[str], interval: float):
    """Watch approvals via MCP notifications/progress; fallback to polling."""
    config = ctx.obj["config"]
    async with CodexClient(config) as client:
        # Try server-side watcher (it emits notifications/progress with kind=codex.approvals)
        try:
            await client.call_tool("codex-watch-approvals", {"session_id": session_id, "interval_s": interval})
            click.echo("Watching approvals (notifications/progress)")
            # In this simple CLI, fall back to polling since we don't hook notifications here
            raise RuntimeError("notifications not wired; polling instead")
        except Exception:
            click.echo("Polling approvals list... Press Ctrl+C to stop")
            try:
                while True:
                    res = await client.call_tool("codex-list-approvals", {"session_id": session_id})
                    sc = getattr(res, "structured_content", None) or getattr(res, "structuredContent", None)
                    click.echo(json.dumps(sc or {}))
                    await asyncio.sleep(interval)
            except KeyboardInterrupt:
                pass


def main():
    """Main entry point"""
    # Run async commands
    def run_async(f):
        def wrapper(*args, **kwargs):
            return asyncio.run(f(*args, **kwargs))
        return wrapper
    
    # Apply async wrapper to async commands
    cli.commands["list-tools"].callback = run_async(cli.commands["list-tools"].callback)
    cli.commands["call-tool"].callback = run_async(cli.commands["call-tool"].callback)
    cli.commands["health"].callback = run_async(cli.commands["health"].callback)
    cli.commands["status"].callback = run_async(cli.commands["status"].callback)
    cli.commands["serve"].callback = run_async(cli.commands["serve"].callback)
    cli.commands["exec"].callback = run_async(cli.commands["exec"].callback)
    cli.commands["exec-stream"].callback = run_async(cli.commands["exec-stream"].callback)
    cli.commands["apply-patch"].callback = run_async(cli.commands["apply-patch"].callback)
    cli.commands["search"].callback = run_async(cli.commands["search"].callback)
    if "mcp" in cli.commands:
        cli.commands["mcp"].callback = run_async(cli.commands["mcp"].callback)
    if "proto" in cli.commands:
        cli.commands["proto"].callback = run_async(cli.commands["proto"].callback)
    if "respond-approval" in cli.commands:
        cli.commands["respond-approval"].callback = run_async(cli.commands["respond-approval"].callback)
    if "watch-approvals" in cli.commands:
        cli.commands["watch-approvals"].callback = run_async(cli.commands["watch-approvals"].callback)
    cli.commands["history"].callback = run_async(cli.commands["history"].callback)
    cli.commands["chat"].callback = run_async(cli.commands["chat"].callback)
    cli.commands["events"].callback = run_async(cli.commands["events"].callback)
    
    cli()


if __name__ == "__main__":
    main()
