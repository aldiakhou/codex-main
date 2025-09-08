"""
Persistent exec session manager for Codex Python.

Provides a minimal API to start a long-lived process, write to stdin,
and stop it. Output streaming can be layered via the owning orchestrator.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Dict, Optional, List
from pathlib import Path


@dataclass
class ExecSession:
    id: str
    process: asyncio.subprocess.Process
    stdout_task: Optional[asyncio.Task]
    stderr_task: Optional[asyncio.Task]


class ExecSessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, ExecSession] = {}

    async def start_session(
        self,
        command: List[str],
        session_id: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        on_output: Optional[callable] = None,
    ) -> str:
        import uuid
        sid = session_id or f"exec_{uuid.uuid4()}"
        env_map = os.environ.copy()
        if env:
            env_map.update(env)

        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(Path(cwd).resolve()) if cwd else None,
            env=env_map,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Background readers that simply drain to avoid blocking; owner can add routing later
        async def _drain(stream, name: str):
            try:
                while True:
                    chunk = await stream.read(8192)
                    if not chunk:
                        break
                    if on_output:
                        try:
                            on_output(name, chunk)
                        except Exception:
                            pass
            except Exception:
                pass

        t_out = asyncio.create_task(_drain(proc.stdout, "stdout")) if proc.stdout else None
        t_err = asyncio.create_task(_drain(proc.stderr, "stderr")) if proc.stderr else None

        self._sessions[sid] = ExecSession(id=sid, process=proc, stdout_task=t_out, stderr_task=t_err)
        return sid

    async def write_stdin(self, session_id: str, data: str) -> None:
        sess = self._sessions.get(session_id)
        if not sess or not sess.process or not sess.process.stdin:
            raise RuntimeError("exec session not found or not writable")
        try:
            sess.process.stdin.write(data.encode())
            await sess.process.stdin.drain()
        except Exception as e:
            raise RuntimeError(f"write_stdin failed: {e}")

    async def stop_session(self, session_id: str) -> None:
        sess = self._sessions.pop(session_id, None)
        if not sess:
            return
        try:
            if sess.process and sess.process.returncode is None:
                sess.process.terminate()
                try:
                    await asyncio.wait_for(sess.process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    sess.process.kill()
        finally:
            for t in (sess.stdout_task, sess.stderr_task):
                if t:
                    t.cancel()
                    try:
                        await t
                    except Exception:
                        pass
