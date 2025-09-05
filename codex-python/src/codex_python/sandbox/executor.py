"""
Sandboxing implementation for Codex Python
Provides platform-specific sandboxing for security
"""

import os
import sys
import subprocess
import structlog
from typing import Dict, List, Optional, Set, Literal, AsyncIterator, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import tempfile
import shutil
from pathlib import Path

logger = structlog.get_logger(__name__)


class SandboxLevel(Enum):
    """Sandbox restriction levels"""
    NONE = "none"                    # No restrictions
    READ_ONLY = "read_only"          # Can read files, no writes
    WORKSPACE = "workspace"          # Can write to workspace only
    RESTRICTED = "restricted"        # Limited network and filesystem
    FULL = "full"                    # Full access (after approval)


@dataclass
class SandboxPolicy:
    """Sandbox policy definition"""
    level: SandboxLevel
    allowed_paths: Set[str] = field(default_factory=set)
    blocked_paths: Set[str] = field(default_factory=set)
    allowed_commands: Set[str] = field(default_factory=set)
    blocked_commands: Set[str] = field(default_factory=set)
    network_allowed: bool = False
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0


@dataclass
class SandboxConfig:
    """Sandbox configuration"""
    enabled: bool = True
    default_level: SandboxLevel = SandboxLevel.WORKSPACE
    platform_specific: bool = True
    temp_dir: Optional[str] = None
    log_commands: bool = True
    strict_mode: bool = True


class SandboxError(Exception):
    """Sandbox-related errors"""
    pass


class SandboxExecutor:
    """Base class for sandboxed execution"""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.platform = self._detect_platform()
    
    def _detect_platform(self) -> str:
        """Detect the current platform"""
        if sys.platform == "darwin":
            return "macos"
        elif sys.platform.startswith("linux"):
            return "linux"
        elif sys.platform == "win32":
            return "windows"
        else:
            return "unknown"
    
    async def execute_command(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        policy: Optional[SandboxPolicy] = None,
        input_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command under sandbox restrictions"""
        
        if not self.config.enabled:
            return await self._execute_unrestricted(command, cwd, env, input_data)
        
        # Use provided policy or create default
        if policy is None:
            policy = self._create_default_policy()
        
        # Validate command against policy
        self._validate_command(command, policy)
        
        # Platform-specific execution
        if self.platform == "macos" and self.config.platform_specific:
            return await self._execute_macos(command, cwd, env, policy, input_data)
        elif self.platform == "linux" and self.config.platform_specific:
            return await self._execute_linux(command, cwd, env, policy, input_data)
        else:
            # Fallback to basic sandboxing
            return await self._execute_basic(command, cwd, env, policy, input_data)

    async def execute_command_stream(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        policy: Optional[SandboxPolicy] = None,
        input_data: Optional[str] = None,
        max_deltas: int = 10_000,
        chunk_size: int = 8192,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Execute a command and yield streamed output chunks.

        Yields dicts of the form {"type": "delta", "stream": "stdout|stderr", "data": bytes}
        followed by a final {"type": "result", ...} summary.
        """
        if not self.config.enabled:
            async for item in self._stream_unrestricted(command, cwd, env, input_data, max_deltas, chunk_size):
                yield item
            return

        # Use provided policy or create default
        policy = policy or self._create_default_policy()
        self._validate_command(command, policy)

        # Stream using basic engine for now
        async for item in self._stream_basic(command, cwd, env, policy, input_data, max_deltas, chunk_size):
            yield item
    
    def _create_default_policy(self) -> SandboxPolicy:
        """Create default sandbox policy"""
        allowed_paths = {os.getcwd()}
        
        if self.config.temp_dir:
            allowed_paths.add(self.config.temp_dir)
        else:
            allowed_paths.add(tempfile.gettempdir())
        
        # Common safe commands
        allowed_commands = {
            "ls", "cat", "echo", "pwd", "which", "type",
            "git", "python", "node", "npm", "pip",
            "grep", "find", "head", "tail", "wc"
        }
        
        # Dangerous commands to block
        blocked_commands = {
            "rm", "sudo", "su", "chmod", "chown",
            "mkfs", "fdisk", "dd", "shutdown", "reboot"
        }
        
        return SandboxPolicy(
            level=self.config.default_level,
            allowed_paths=allowed_paths,
            allowed_commands=allowed_commands,
            blocked_commands=blocked_commands,
            network_allowed=False,
            environment={"PATH": os.environ.get("PATH", "")}
        )
    
    def _validate_command(self, command: List[str], policy: SandboxPolicy) -> None:
        """Validate command against sandbox policy"""
        if not command:
            raise SandboxError("Empty command")
        
        cmd_name = Path(command[0]).name
        
        # Check blocked commands
        if cmd_name in policy.blocked_commands:
            raise SandboxError(f"Command '{cmd_name}' is blocked by sandbox policy")
        
        # Check allowed commands for restricted levels
        if policy.level in [SandboxLevel.RESTRICTED, SandboxLevel.READ_ONLY]:
            if cmd_name not in policy.allowed_commands:
                raise SandboxError(f"Command '{cmd_name}' is not allowed in {policy.level.value} sandbox")
        
        # Validate arguments for potentially dangerous operations
        self._validate_arguments(command, policy)
    
    def _validate_arguments(self, command: List[str], policy: SandboxPolicy) -> None:
        """Validate command arguments for dangerous patterns"""
        cmd_name = Path(command[0]).name
        
        # Check for dangerous argument patterns
        dangerous_patterns = [
            ("rm", ["-rf", "--no-preserve-root"]),
            ("chmod", ["777", "+x"]),
            ("chown", []),
            ("dd", ["of="]),
            ("find", ["-exec", "-delete"]),
        ]
        
        for dangerous_cmd, dangerous_args in dangerous_patterns:
            if cmd_name == dangerous_cmd:
                for arg in command[1:]:
                    for dangerous_arg in dangerous_args:
                        if dangerous_arg in arg:
                            raise SandboxError(f"Dangerous argument pattern detected: {arg}")
        
        # Check path arguments for write operations
        if policy.level in [SandboxLevel.READ_ONLY, SandboxLevel.WORKSPACE]:
            write_indicators = ["-o", "--output", ">", ">>", "-w", "--write"]
            for i, arg in enumerate(command):
                if arg in write_indicators and i + 1 < len(command):
                    path = command[i + 1]
                    self._validate_path_access(path, policy, write=True)
    
    def _validate_path_access(self, path: str, policy: SandboxPolicy, write: bool = False) -> None:
        """Validate file system access"""
        if not path:
            return
        
        path = os.path.abspath(path)
        
        # Check blocked paths
        for blocked_path in policy.blocked_paths:
            if path.startswith(os.path.abspath(blocked_path)):
                raise SandboxError(f"Access to path '{path}' is blocked by sandbox policy")
        
        # For write operations, check allowed paths
        if write and policy.level in [SandboxLevel.READ_ONLY, SandboxLevel.WORKSPACE]:
            allowed = False
            for allowed_path in policy.allowed_paths:
                if path.startswith(os.path.abspath(allowed_path)):
                    allowed = True
                    break
            
            if not allowed:
                raise SandboxError(f"Write access to '{path}' not allowed in {policy.level.value} sandbox")
    
    async def _execute_unrestricted(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        input_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute command without restrictions"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None
            )
            
            stdout, stderr = await process.communicate(
                input=input_data.encode() if input_data else None
            )
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "success": process.returncode == 0,
                "sandboxed": False
            }
            
        except Exception as e:
            logger.error("Command execution failed", command=command, error=str(e))
            raise SandboxError(f"Command execution failed: {e}")
    
    async def _execute_basic(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        policy: Optional[SandboxPolicy] = None,
        input_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Basic sandbox execution using subprocess restrictions"""
        
        if policy is None:
            policy = self._create_default_policy()
        # Merge environment variables
        exec_env = policy.environment.copy()
        if env:
            exec_env.update(env)
        
        # Restrict environment
        if policy.level == SandboxLevel.RESTRICTED:
            # Remove potentially dangerous env vars
            safe_env = {}
            for key, value in exec_env.items():
                if key.upper() not in ["PATH", "HOME", "USER", "SHELL"]:
                    continue
                safe_env[key] = value
            exec_env = safe_env
        
        # Execute with basic restrictions
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                env=exec_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode() if input_data else None),
                timeout=policy.timeout
            )
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "success": process.returncode == 0,
                "sandboxed": True,
                "level": policy.level.value
            }
            
        except asyncio.TimeoutError:
            try:
                process.kill()
            except:
                pass
            raise SandboxError(f"Command timed out after {policy.timeout} seconds")
        
        except Exception as e:
            logger.error("Basic sandbox execution failed", command=command, error=str(e))
            raise SandboxError(f"Sandbox execution failed: {e}")

    async def _stream_unrestricted(
        self,
        command: List[str],
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        input_data: Optional[str],
        max_deltas: int,
        chunk_size: int,
    ) -> AsyncIterator[Dict[str, Any]]:
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None
            )

            if input_data:
                await process.stdin.write(input_data.encode())
                await process.stdin.drain()
                process.stdin.close()

            emitted = 0

            async def pump(stream, name, queue: asyncio.Queue):
                nonlocal emitted
                while True:
                    chunk = await stream.read(chunk_size)
                    if not chunk:
                        break
                    if emitted < max_deltas:
                        emitted += 1
                        await queue.put({"type": "delta", "stream": name, "data": chunk})

            q: asyncio.Queue = asyncio.Queue()
            t1 = asyncio.create_task(pump(process.stdout, "stdout", q))
            t2 = asyncio.create_task(pump(process.stderr, "stderr", q))

            while any(not t.done() for t in (t1, t2)) or not q.empty():
                try:
                    item = await asyncio.wait_for(q.get(), timeout=0.05)
                    yield item
                except asyncio.TimeoutError:
                    await asyncio.sleep(0)

            rc = await process.wait()
            yield {"type": "result", "returncode": rc}
        except Exception as e:
            yield {"type": "error", "message": str(e)}

    async def _stream_basic(
        self,
        command: List[str],
        cwd: Optional[str],
        env: Optional[Dict[str, str]],
        policy: SandboxPolicy,
        input_data: Optional[str],
        max_deltas: int,
        chunk_size: int,
    ) -> AsyncIterator[Dict[str, Any]]:
        try:
            exec_env = policy.environment.copy()
            if env:
                exec_env.update(env)

            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                env=exec_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None
            )

            if input_data:
                await process.stdin.write(input_data.encode())
                await process.stdin.drain()
                process.stdin.close()

            emitted = 0

            async def pump(stream, name, queue: asyncio.Queue):
                nonlocal emitted
                while True:
                    chunk = await stream.read(chunk_size)
                    if not chunk:
                        break
                    if emitted < max_deltas:
                        emitted += 1
                        await queue.put({"type": "delta", "stream": name, "data": chunk})

            q: asyncio.Queue = asyncio.Queue()
            t1 = asyncio.create_task(pump(process.stdout, "stdout", q))
            t2 = asyncio.create_task(pump(process.stderr, "stderr", q))

            while any(not t.done() for t in (t1, t2)) or not q.empty():
                try:
                    item = await asyncio.wait_for(q.get(), timeout=0.05)
                    yield item
                except asyncio.TimeoutError:
                    await asyncio.sleep(0)

            rc = await process.wait()
            yield {"type": "result", "returncode": rc, "sandboxed": True, "level": policy.level.value}
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    async def _execute_macos(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        policy: Optional[SandboxPolicy] = None,
        input_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """macOS-specific sandbox execution using seatbelt"""
        if policy is None:
            policy = self._create_default_policy()
        
        # Build seatbelt profile
        profile = self._build_seatbelt_profile(policy)
        
        try:
            # Write profile to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sb', delete=False) as f:
                f.write(profile)
                profile_path = f.name
            
            # Execute with sandbox-exec
            sandbox_cmd = ["sandbox-exec", "-f", profile_path] + command
            
            result = await self._execute_basic(sandbox_cmd, cwd, env, policy, input_data)
            result["sandbox_engine"] = "seatbelt"
            
            return result
            
        except Exception as e:
            logger.warning("macOS seatbelt execution failed, falling back to basic", error=str(e))
            return await self._execute_basic(command, cwd, env, policy, input_data)
        
        finally:
            # Clean up profile file
            try:
                os.unlink(profile_path)
            except:
                pass
    
    def _build_seatbelt_profile(self, policy: SandboxPolicy) -> str:
        """Build macOS seatbelt sandbox profile"""
        
        profile = '(version 1)\n'
        
        # Allow command execution
        profile += '(allow default)\n'
        
        # Path restrictions
        if policy.level == SandboxLevel.READ_ONLY:
            profile += '(deny file-write*)\n'
            profile += '(allow file-read*)\n'
            
            # Allow specific paths
            for path in policy.allowed_paths:
                profile += f'(allow file-read* (subpath "{path}"))\n'
        
        elif policy.level == SandboxLevel.WORKSPACE:
            # Allow write to workspace
            for path in policy.allowed_paths:
                profile += f'(allow file-write* (subpath "{path}"))\n'
                profile += f'(allow file-read* (subpath "{path}"))\n'
        
        # Network restrictions
        if not policy.network_allowed:
            profile += '(deny network*)\n'
        
        # Process restrictions
        profile += '(deny process-exec\n'
        for cmd in policy.blocked_commands:
            profile += f'    (regex "^{cmd}$")\n'
        profile += ')\n'
        
        return profile
    
    async def _execute_linux(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        policy: Optional[SandboxPolicy] = None,
        input_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Linux-specific sandbox execution (placeholder for landlock)"""
        if policy is None:
            policy = self._create_default_policy()
        
        # For now, fall back to basic sandboxing
        # In a full implementation, this would use landlock or seccomp
        logger.info("Linux sandbox execution using basic restrictions")
        
        result = await self._execute_basic(command, cwd, env, policy, input_data)
        result["sandbox_engine"] = "basic"
        
        return result
    
    async def create_sandbox_environment(self, policy: Optional[SandboxPolicy] = None) -> Dict[str, Any]:
        """Create a sandboxed environment for execution"""
        
        if policy is None:
            policy = self._create_default_policy()
        
        # Create temporary directory if needed
        temp_dir = None
        if self.config.temp_dir:
            temp_dir = tempfile.mkdtemp(prefix="codex_sandbox_", dir=self.config.temp_dir)
            policy.allowed_paths.add(temp_dir)
        else:
            temp_dir = tempfile.mkdtemp(prefix="codex_sandbox_")
            policy.allowed_paths.add(temp_dir)
        
        # Create restricted environment
        env = policy.environment.copy()
        env.update({
            "SANDBOX_LEVEL": policy.level.value,
            "SANDBOX_TEMP": temp_dir,
            "PYTHONPATH": "",  # Clear Python path for isolation
        })
        
        return {
            "temp_dir": temp_dir,
            "environment": env,
            "policy": policy,
            "cleanup": lambda: shutil.rmtree(temp_dir, ignore_errors=True)
        }
    
    async def cleanup_sandbox_environment(self, env_info: Dict[str, Any]) -> None:
        """Clean up sandbox environment"""
        if "cleanup" in env_info:
            env_info["cleanup"]()


class SandboxManager:
    """Manages sandbox policies and execution"""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.executor = SandboxExecutor(config)
        self.active_sessions: Dict[str, Dict] = {}
    
    async def execute_with_approval(
        self,
        command: List[str],
        session_id: str,
        approval_callback = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute command with approval workflow"""
        
        # Get session policy
        session_info = self.active_sessions.get(session_id, {})
        policy = session_info.get("policy", self.executor._create_default_policy())
        
        # Check if command requires approval
        requires_approval = self._requires_approval(command, policy)
        
        if requires_approval and approval_callback:
            approved = await approval_callback(command, policy)
            if not approved:
                raise SandboxError(f"Command execution not approved: {' '.join(command)}")
        
        # Execute command
        result = await self.executor.execute_command(command, policy=policy, **kwargs)
        
        # Log execution if enabled
        if self.config.log_commands:
            logger.info(
                "Sandbox command executed",
                command=command,
                session=session_id,
                result=result.get("success"),
                sandboxed=result.get("sandboxed", False)
            )
        
        return result
    
    def _requires_approval(self, command: List[str], policy: SandboxPolicy) -> bool:
        """Check if command requires approval"""
        cmd_name = Path(command[0]).name
        
        # Commands that always require approval
        high_risk_commands = {
            "rm", "sudo", "su", "chmod", "chown", "mkfs",
            "fdisk", "dd", "format", "del", "rmdir"
        }
        
        if cmd_name in high_risk_commands:
            return True
        
        # Check for risky arguments
        risky_patterns = ["-rf", "--no-preserve-root", "/dev/", "/sys/", "/proc/"]
        for arg in command[1:]:
            for pattern in risky_patterns:
                if pattern in arg:
                    return True
        
        return False
    
    def create_session(self, session_id: str, policy: Optional[SandboxPolicy] = None) -> None:
        """Create a sandbox session"""
        self.active_sessions[session_id] = {
            "policy": policy or self.executor._create_default_policy(),
            "created_at": asyncio.get_event_loop().time()
        }
    
    def close_session(self, session_id: str) -> None:
        """Close a sandbox session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def get_session_policy(self, session_id: str) -> Optional[SandboxPolicy]:
        """Get policy for a session"""
        session = self.active_sessions.get(session_id)
        return session.get("policy") if session else None
    
    async def cleanup_all_sessions(self) -> None:
        """Clean up all active sessions"""
        for session_id in list(self.active_sessions.keys()):
            self.close_session(session_id)
