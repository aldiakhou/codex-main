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


@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
@click.option("--log-level", default="INFO", help="Log level (DEBUG, INFO, WARNING, ERROR)")
@click.pass_context
def cli(ctx, config, log_level):
    """Cadenza - Model Context Protocol Client"""
    ctx.ensure_object(dict)
    
    # Set log level
    import logging
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    # Load configuration
    if config:
        ctx.obj["config"] = Config.from_file(config)
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
        
        ctx.obj["config"] = config_obj


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
    """Execute a command with approval/sandboxing."""
    config = ctx.obj["config"]
    env_dict = {}
    for kv in env:
        if "=" in kv:
            k, v = kv.split("=", 1)
            env_dict[k] = v
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
@click.pass_context
async def exec_stream(ctx, cmd, cwd, env):
    """Stream command output live."""
    config = ctx.obj["config"]
    env_dict = {}
    for kv in env:
        if "=" in kv:
            k, v = kv.split("=", 1)
            env_dict[k] = v
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


@cli.command(name="apply-patch")
@click.option("--file", "patch_file", type=click.Path(exists=True), help="Patch file path (defaults to stdin)")
@click.option("--root", "root_path", type=click.Path(), help="Patch root path")
@click.pass_context
async def apply_patch_cmd(ctx, patch_file, root_path):
    """Apply a unified diff patch (reads stdin if --file is not given)."""
    config = ctx.obj["config"]
    patch_text = ""
    if patch_file:
        patch_text = Path(patch_file).read_text(encoding="utf-8")
    else:
        patch_text = sys.stdin.read()
    from .core.orchestrator import CodexOrchestrator
    orch = CodexOrchestrator(config)
    await orch.initialize()
    try:
        res = await orch.apply_patch(patch_text, root_path=root_path)
        if res.success:
            click.echo("Patch applied successfully")
            sys.exit(0)
        else:
            click.echo(f"Patch failed: {res.error}")
            sys.exit(1)
    finally:
        await orch.cleanup()


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
@click.option("--stream/--no-stream", default=True, help="Stream responses")
@click.pass_context
async def chat(ctx, prompt, stream):
    """Chat with LLM (uses built-in tool loop)."""
    config = ctx.obj["config"]
    from .core.orchestrator import CodexOrchestrator
    orch = CodexOrchestrator(config)
    await orch.initialize()
    try:
        text = " ".join(prompt)
        gen = orch.chat([{"role": "user", "content": text}], stream=stream)

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
    finally:
        await orch.cleanup()


@cli.command()
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.pass_context
async def serve(ctx, host, port):
    """Start Codex as a service"""
    config = ctx.obj["config"]
    
    click.echo(f"Starting Codex service on {host}:{port}")
    click.echo("Press Ctrl+C to stop")
    
    # This would start an HTTP server - placeholder for now
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nShutting down...")


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
    cli.commands["history"].callback = run_async(cli.commands["history"].callback)
    cli.commands["chat"].callback = run_async(cli.commands["chat"].callback)
    
    cli()


if __name__ == "__main__":
    main()
