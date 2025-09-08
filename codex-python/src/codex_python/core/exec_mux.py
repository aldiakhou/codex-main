"""
Local exec multiplexer: simple TCP JSON control channel for cross-process
stdin writes and session control.

Security: binds to 127.0.0.1 only. No auth. Intended for local development.
"""

from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable, Optional


class LocalExecMux:
    def __init__(
        self,
        write_cb: Callable[[str, bytes], Awaitable[None]],
        stop_cb: Callable[[str], Awaitable[None]],
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        token: Optional[str] = None,
    ) -> None:
        self._write_cb = write_cb
        self._stop_cb = stop_cb
        self._host = host
        self._port = port or 0
        self._server: Optional[asyncio.base_events.Server] = None
        self._token = token or ""

    async def start(self) -> int:
        self._server = await asyncio.start_server(self._handle_client, self._host, self._port)
        sock = next(iter(self._server.sockets or []), None)
        return int(sock.getsockname()[1]) if sock else 0

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            data = await reader.read(1_000_000)
            req = json.loads(data.decode('utf-8'))
            op = req.get('op')
            # Capability token check
            if self._token:
                if req.get('token') != self._token:
                    resp = {"ok": False, "error": "unauthorized"}
                    writer.write((json.dumps(resp) + "\n").encode('utf-8'))
                    await writer.drain()
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass
                    return
            if op == 'write_stdin':
                sid = req.get('session_id')
                b64 = req.get('data_b64') or ""
                import base64
                try:
                    payload = base64.b64decode(b64)
                except Exception:
                    payload = b""
                await self._write_cb(sid, payload)
                resp = {"ok": True}
            elif op == 'stop':
                sid = req.get('session_id')
                await self._stop_cb(sid)
                resp = {"ok": True}
            elif op == 'ping':
                resp = {"ok": True, "pong": True}
            else:
                resp = {"ok": False, "error": "unknown op"}
        except Exception as e:
            resp = {"ok": False, "error": str(e)}
        writer.write((json.dumps(resp) + "\n").encode('utf-8'))
        await writer.drain()
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
