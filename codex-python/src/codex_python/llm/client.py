"""
LLM Client implementation for Codex Python
Supports OpenAI, Ollama, and other providers with streaming and tool use
"""

import asyncio
import json
import structlog
from typing import Dict, List, Optional, Any, AsyncIterator, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import httpx
import aiohttp
from abc import ABC, abstractmethod

# Prefer the official OpenAI SDK when available; fall back gracefully when not
try:  # pragma: no cover - optional dependency
    from openai import AsyncOpenAI  # type: ignore
    try:
        from openai import pydantic_function_tool as _pydantic_function_tool  # type: ignore
    except Exception:  # pragma: no cover
        _pydantic_function_tool = None  # type: ignore
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore
    _pydantic_function_tool = None  # type: ignore

logger = structlog.get_logger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class LLMMessage:
    """Message for LLM conversation"""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    # Optional list of image file paths to attach (multi-modal)
    images: Optional[List[str]] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMTool:
    """Tool definition for LLM function calling"""
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: bool = False
    pydantic_model: Optional[Any] = None


@dataclass
class LLMToolCall:
    """Tool call from LLM"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    tool_calls: List[LLMToolCall] = field(default_factory=list)
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    # Optional model-provided reasoning fields (when available)
    reasoning_delta: Optional[str] = None
    reasoning_raw_delta: Optional[str] = None
    # Optional tool result payload (when provider streams tool outputs)
    tool_result_delta: Optional[str] = None


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: float = 60.0
    max_retries: int = 3
    streaming: bool = True
    # Prefer OpenAI Responses API for richer reasoning (when tools are not used)
    use_responses_api: bool = False
    # Optional default vision model to use for image turns when the primary
    # model is not vision-capable.
    default_vision_model: Optional[str] = None


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)
    
    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncIterator[LLMResponse]]:
        """Send chat messages to LLM"""
        pass
    
    @abstractmethod
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        pass
    
    async def close(self) -> None:
        """Close the client"""
        await self.client.aclose()

    # Retry/backoff helpers for network requests
    async def _post_with_retries(self, url: str, *, json: Dict, headers: Dict[str, str]) -> httpx.Response:
        max_retries = getattr(self.config, 'max_retries', 3) or 1
        base_delay = 0.5
        import time as _time
        for attempt in range(max_retries):
            try:
                t0 = _time.perf_counter()
                resp = await self.client.post(url, json=json, headers=headers)
                try:
                    resp.raise_for_status()
                    logger.debug("llm_post_ok", url=url, status=resp.status_code, attempt=attempt, elapsed=_time.perf_counter()-t0)
                    return resp
                except httpx.HTTPStatusError as e:
                    code = e.response.status_code if e.response is not None else None
                    # For concise diagnostics on 4xx, include a short body snippet.
                    body_snippet = None
                    try:
                        if e.response is not None and code is not None and 400 <= code < 500:
                            text = await e.response.aread()
                            body_snippet = (text[:1024]).decode(errors="replace") if isinstance(text, (bytes, bytearray)) else str(text)[:1024]
                    except Exception:
                        pass
                    logger.debug("llm_post_status_error", url=url, status=code, attempt=attempt, elapsed=_time.perf_counter()-t0, body=body_snippet)
                    if attempt >= max_retries - 1 or not (code == 429 or (code is not None and code >= 500)):
                        raise
            except (httpx.TransportError, httpx.TimeoutException) as e:
                logger.debug("llm_post_transport_error", url=url, attempt=attempt)
                if attempt >= max_retries - 1:
                    raise
            await asyncio.sleep(base_delay * (2 ** attempt) + 0.05 * attempt)

    async def _enter_stream_with_retries(self, url: str, *, json: Dict, headers: Dict[str, str]):
        """Return (cm, response) with retries on 429/5xx and transport errors."""
        max_retries = getattr(self.config, 'max_retries', 3) or 1
        base_delay = 0.5
        import time as _time
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries):
            cm = self.client.stream("POST", url, json=json, headers=headers)
            try:
                t0 = _time.perf_counter()
                resp = await cm.__aenter__()
                code = resp.status_code
                if code >= 400 and not (code == 429 or code >= 500):
                    # non-retryable HTTP error, include short body snippet
                    body_snippet = None
                    try:
                        text = await resp.aread()
                        body_snippet = (text[:1024]).decode(errors="replace") if isinstance(text, (bytes, bytearray)) else str(text)[:1024]
                    except Exception:
                        pass
                    logger.debug("llm_stream_http_error", url=url, status=code, attempt=attempt, elapsed=_time.perf_counter()-t0, body=body_snippet)
                    await cm.__aexit__(None, None, None)
                    raise httpx.HTTPStatusError("HTTP error", request=None, response=resp)
                logger.debug("llm_stream_ok", url=url, status=code, attempt=attempt, elapsed=_time.perf_counter()-t0)
                return cm, resp
            except (httpx.TransportError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_exc = e
                try:
                    await cm.__aexit__(None, None, None)
                except Exception:
                    pass
                if attempt >= max_retries - 1:
                    break
                await asyncio.sleep(base_delay * (2 ** attempt) + 0.05 * attempt)
        if last_exc:
            raise last_exc
        raise RuntimeError("exhausted retries for stream")

    # Compose headers for the Responses API (requires beta header on raw HTTP paths).
    def _responses_headers(self) -> Dict[str, str]:
        base = dict(getattr(self, "headers", {}) or {})
        # Align with codex-rs behaviour: opt into Responses beta when not using SDK
        base.setdefault("OpenAI-Beta", "responses=experimental")
        return base

    # Extract plain text from nested Responses output structures.
    @staticmethod
    def _flatten_text(node: Any) -> str:
        if node is None:
            return ""
        if isinstance(node, str):
            return node
        if isinstance(node, (bytes, bytearray)):
            try:
                return node.decode("utf-8", errors="replace")
            except Exception:
                return str(node)
        if isinstance(node, list):
            return "".join(LLMClient._flatten_text(x) for x in node)
        if isinstance(node, dict):
            # Prefer explicit fields first
            for key in ("output_text", "text", "content", "delta"):
                if key in node:
                    return LLMClient._flatten_text(node.get(key))
            # Fallback: concatenate any stringly fields
            acc = []
            for v in node.values():
                acc.append(LLMClient._flatten_text(v))
            return "".join(acc)
        # Fallback to string
        return str(node)

    # Helpers for multi-modal (encode local image path to data URL)
    @staticmethod
    def _path_to_data_url(path: str) -> Optional[str]:
        try:
            import base64, mimetypes, os
            if not path:
                return None
            mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except Exception:
            return None


class OpenAIClient(LLMClient):
    """OpenAI API client"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        # Best-effort initialization of the official SDK for streaming
        self._sdk = None
        if AsyncOpenAI is not None and config.api_key:
            try:
                sdk_kwargs: Dict[str, Any] = {"api_key": config.api_key}
                if config.base_url:
                    sdk_kwargs["base_url"] = config.base_url
                self._sdk = AsyncOpenAI(**sdk_kwargs)  # type: ignore[call-arg]
            except Exception:
                # swallow and continue with httpx paths
                self._sdk = None
    
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncIterator[LLMResponse]]:
        """Send chat messages to OpenAI"""
        # If any message includes images, prefer the Responses API and ensure
        # a vision-capable model. Fallback to gpt-4o-mini when the configured
        # model does not appear to support vision.
        has_images = any(bool(m.images) for m in messages)
        vision_model = self.config.model
        if has_images and not any(x in (self.config.model or "").lower() for x in ("gpt-4o",)):
            # Prefer configured default vision model when provided
            dv = getattr(self.config, 'default_vision_model', None)
            vision_model = dv or "gpt-4o-mini"

        # Prefer the Responses API for richer reasoning when enabled or when
        # images are present.
        if getattr(self.config, 'use_responses_api', False) or has_images:
            tools_for_turn = None if has_images else tools
            if stream:
                # Use Responses streaming when images are present; prefer SDK
                # when available, otherwise SSE fallback.
                return self._stream_chat_responses(messages, tools=tools_for_turn, model_override=vision_model)
            else:
                return await self._non_stream_chat_responses(messages, tools=tools_for_turn, model_override=vision_model)

        # Convert messages to OpenAI format (multi-modal support via content list)
        openai_messages = []
        for msg in messages:
            content: Union[str, List[Dict[str, Any]]]
            if msg.images:
                parts: List[Dict[str, Any]] = []
                if msg.content:
                    parts.append({"type": "text", "text": msg.content})
                for p in (msg.images or []):
                    data_url = self._path_to_data_url(p)
                    if data_url:
                        parts.append({"type": "image_url", "image_url": {"url": data_url}})
                content = parts if parts else msg.content
            else:
                content = msg.content
            openai_msg = {"role": msg.role, "content": content}
            if msg.tool_calls:
                openai_msg["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
            openai_messages.append(openai_msg)
        
        # Prepare request payload
        payload = {
            "model": self.config.model,
            "messages": openai_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": stream
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                }
                for tool in tools
            ]
        
        if stream:
            # Prefer SDK streaming when tools are absent or declared strict;
            # otherwise fall back to HTTP streaming to avoid SDK auto-parse
            # strictness requirements.
            if self._sdk is not None:
                all_strict = (not tools) or all(getattr(t, "strict", False) for t in (tools or []))
                if all_strict:
                    return self._stream_chat_via_sdk(messages, tools)
            return self._stream_chat(payload)
        else:
            # Prefer SDK parse() when all tools are strict Pydantic function tools.
            if self._sdk is not None and tools:
                all_pydantic = all(getattr(t, "pydantic_model", None) is not None and getattr(t, "strict", False) for t in tools)
                if all_pydantic and _pydantic_function_tool is not None:
                    try:
                        return await self._non_stream_chat_via_sdk_parse(messages, tools)
                    except Exception:
                        pass
            if getattr(self.config, 'use_responses_api', False) and self._sdk is not None:
                # When using Responses API in non-stream mode and SDK is
                # available, route through SDK for richer typed responses.
                try:
                    return await self._non_stream_responses_via_sdk(messages, tools)
                except Exception:
                    pass
            if self._sdk is not None:
                try:
                    return await self._non_stream_chat_via_sdk(messages, tools)
                except Exception:
                    pass
            return await self._non_stream_chat(payload)

    def _responses_tools_payload(self, tools: Optional[List[LLMTool]]) -> Optional[List[Dict]]:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    # --- SDK-powered helpers (Chat/Responses) ---------------------------------

    def _format_chat_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for msg in messages:
            content: Union[str, List[Dict[str, Any]]]
            if msg.images:
                parts: List[Dict[str, Any]] = []
                if msg.content:
                    parts.append({"type": "text", "text": msg.content})
                for p in (msg.images or []):
                    data_url = self._path_to_data_url(p)
                    if data_url:
                        parts.append({"type": "image_url", "image_url": {"url": data_url}})
                content = parts if parts else msg.content
            else:
                content = msg.content
            m = {"role": msg.role, "content": content}
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            out.append(m)
        return out

    def _format_chat_tools(self, tools: Optional[List[LLMTool]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None
        out: List[Dict[str, Any]] = []
        for tool in tools:
            fn: Dict[str, Any] = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            # Only include strict when requested. Some external schemas may
            # not be fully strict-compatible; omitting the flag is safer.
            if getattr(tool, "strict", False):
                fn["strict"] = True
            out.append({"type": "function", "function": fn})
        return out

    async def _non_stream_chat_via_sdk(self, messages: List[LLMMessage], tools: Optional[List[LLMTool]]) -> LLMResponse:
        assert self._sdk is not None
        res = await self._sdk.chat.completions.create(  # type: ignore[union-attr]
            model=self.config.model,
            messages=self._format_chat_messages(messages),
            tools=self._format_chat_tools(tools),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        choice = res.choices[0]
        content = getattr(choice.message, "content", None)
        text = content if isinstance(content, str) else ("" if content is None else str(content))
        tool_calls: List[LLMToolCall] = []
        for tc in getattr(choice.message, "tool_calls", []) or []:
            fn = getattr(tc, "function", None)
            name = getattr(fn, "name", None)
            args = getattr(fn, "arguments", None)
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw": args}
            if name:
                tool_calls.append(LLMToolCall(id=getattr(tc, "id", ""), name=name, arguments=args or {}))
        return LLMResponse(content=text, tool_calls=tool_calls)

    async def _non_stream_chat_via_sdk_parse(self, messages: List[LLMMessage], tools: List[LLMTool]) -> LLMResponse:
        """Use AsyncOpenAI chat.completions.parse with Pydantic tools to auto-parse.

        Preconditions: every tool has pydantic_model and strict=True.
        """
        assert self._sdk is not None and _pydantic_function_tool is not None
        tool_defs = [_pydantic_function_tool(t.pydantic_model) for t in tools]  # type: ignore[arg-type]
        res = await self._sdk.chat.completions.parse(  # type: ignore[union-attr]
            model=self.config.model,
            messages=self._format_chat_messages(messages),
            tools=tool_defs,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        choice = res.choices[0]
        content = getattr(choice.message, "content", None)
        text = content if isinstance(content, str) else ("" if content is None else str(content))
        tool_calls: List[LLMToolCall] = []
        for tc in getattr(choice.message, "tool_calls", []) or []:
            fn = getattr(tc, "function", None)
            name = getattr(fn, "name", None)
            parsed = getattr(fn, "parsed_arguments", None)
            args: Any = {}
            if parsed is not None:
                if hasattr(parsed, "model_dump"):
                    args = parsed.model_dump()
                elif isinstance(parsed, dict):
                    args = parsed
                else:
                    args = {"value": str(parsed)}
            if name:
                tool_calls.append(LLMToolCall(id=getattr(tc, "id", ""), name=name, arguments=args))
        return LLMResponse(content=text, tool_calls=tool_calls)

    async def _non_stream_responses_via_sdk(self, messages: List[LLMMessage], tools: Optional[List[LLMTool]]) -> LLMResponse:
        assert self._sdk is not None
        input_items: List[Dict[str, Any]] = []
        for m in messages:
            if m.images:
                parts: List[Dict[str, Any]] = []
                if m.content:
                    parts.append({"type": "input_text", "text": m.content})
                for p in (m.images or []):
                    data_url = self._path_to_data_url(p)
                    if data_url:
                        parts.append({"type": "input_image", "image_url": data_url})
                input_items.append({"role": m.role, "content": parts})
            else:
                input_items.append({"role": m.role, "content": m.content})
        res = await self._sdk.responses.create(  # type: ignore[union-attr]
            model=self.config.model,
            input=input_items,
            tools=self._responses_tools_payload(tools),
            tool_choice=("auto" if tools else None),
        )
        content = getattr(res, "output_text", None)
        if not isinstance(content, str):
            try:
                data = res.model_dump()
                content = data.get("output_text") if isinstance(data, dict) else None
            except Exception:
                content = None
        return LLMResponse(content=content or "")

    def _stream_chat_via_sdk(self, messages: List[LLMMessage], tools: Optional[List[LLMTool]]) -> AsyncIterator[LLMResponse]:
        assert self._sdk is not None

        async def _gen() -> AsyncIterator[LLMResponse]:
            content_buffer = ""
            try:
                async with self._sdk.chat.completions.stream(  # type: ignore[union-attr]
                    model=self.config.model,
                    messages=self._format_chat_messages(messages),
                    tools=self._format_chat_tools(tools),
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                ) as stream:
                    async for event in stream:
                        if getattr(event, "type", None) == "content.delta":
                            delta = getattr(event, "content", "")
                            if isinstance(delta, str) and delta:
                                content_buffer += delta
                                yield LLMResponse(content=content_buffer)
                    try:
                        completion = await stream.get_final_completion()
                        choice = completion.choices[0]
                        tcalls: List[LLMToolCall] = []
                        for tc in getattr(choice.message, "tool_calls", []) or []:
                            fn = getattr(tc, "function", None)
                            name = getattr(fn, "name", None)
                            args = getattr(fn, "arguments", None)
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except Exception:
                                    args = {"raw": args}
                            if name:
                                tcalls.append(LLMToolCall(id=getattr(tc, "id", ""), name=name, arguments=args or {}))
                        if tcalls:
                            yield LLMResponse(content=content_buffer, tool_calls=tcalls)
                    except Exception:
                        pass
            except Exception as e:
                logger.error("OpenAI Chat (SDK stream) error", error=str(e))
                return

        return _gen()

    async def _non_stream_chat_responses(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        model_override: Optional[str] = None,
    ) -> LLMResponse:
        # Prefer SDK when available for typed handling
        if getattr(self, "_sdk", None) is not None:
            try:
                return await self._non_stream_responses_via_sdk(messages, tools)
            except Exception:
                pass
        # Build structured input with multi-modal support
        # Map system messages to `instructions` field rather than input items.
        instructions_parts: List[str] = []
        input_items: List[Dict[str, Any]] = []
        for m in messages:
            if m.role == "system" and m.content:
                instructions_parts.append(m.content)
                continue
            if m.images:
                parts: List[Dict[str, Any]] = []
                if m.content:
                    parts.append({"type": "input_text", "text": m.content})
                for p in (m.images or []):
                    data_url = self._path_to_data_url(p)
                    if data_url:
                        parts.append({"type": "input_image", "image_url": data_url})
                input_items.append({"role": m.role, "content": parts})
            else:
                input_items.append({"role": m.role, "content": m.content})
        model = model_override or self.config.model
        payload: Dict[str, Any] = {
            "model": model,
            "input": input_items,
        }
        if instructions_parts:
            payload["instructions"] = "\n\n".join(instructions_parts)
        tool_defs = self._responses_tools_payload(tools)
        if tool_defs:
            payload["tools"] = tool_defs
            payload["tool_choice"] = "auto"
        try:
            response = await self._post_with_retries(
                f"{self.base_url}/responses",
                json=payload,
                headers=self._responses_headers(),
            )
            data = response.json()

            # Prefer output_text; otherwise flatten output items recursively
            content_raw = data.get("output_text")
            content = content_raw if isinstance(content_raw, str) else ""
            if not content:
                content = self._flatten_text(data.get("output"))

            # Reasoning may be present in vendor fields
            reasoning_raw = None
            if isinstance(data.get("reasoning"), str):
                reasoning_raw = data.get("reasoning")
            elif isinstance(data.get("reasoning_content"), str):
                reasoning_raw = data.get("reasoning_content")

            # Tool calls (non-stream): search output items for tool call structures
            tool_calls: List[LLMToolCall] = []
            output_items = data.get("output", []) or []
            for item in output_items:
                # Heuristics: item like {type: 'tool_call', id, name, arguments}
                if isinstance(item, dict) and (item.get("type") in ("tool_call", "function_call") or ("name" in item and "arguments" in item)):
                    try:
                        args = item.get("arguments")
                        if isinstance(args, str):
                            args = json.loads(args)
                        elif not isinstance(args, dict):
                            args = {}
                        tool_calls.append(LLMToolCall(
                            id=item.get("id") or "",
                            name=item.get("name") or item.get("function", {}).get("name", ""),
                            arguments=args,
                        ))
                    except Exception:
                        continue

            # Tool result mapping to assistant message when present in output items
            for item in output_items:
                if isinstance(item, dict) and item.get("type") in ("tool_result", "output_tool", "tool_output"):
                    part = item.get("content") or item.get("text") or ""
                    if isinstance(part, dict):
                        part = part.get("content", "")
                    if part:
                        content += ("\n" if content else "") + str(part)

            return LLMResponse(content=content, reasoning_raw_delta=reasoning_raw, tool_calls=tool_calls)
        except Exception as e:
            logger.error("OpenAI Responses (non-stream) error", error=str(e))
            # Fall back to empty response on failure
            return LLMResponse(content="")

    async def _stream_chat_responses(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        model_override: Optional[str] = None,
    ) -> AsyncIterator[LLMResponse]:
        # Prefer SDK streaming when available; otherwise fall back to SSE.
        if getattr(self, "_sdk", None) is not None:
            async def _gen() -> AsyncIterator[LLMResponse]:
                try:
                    # If SDK does not expose responses.stream, use non-stream as single yield
                    if not hasattr(self._sdk, "responses") or not hasattr(self._sdk.responses, "stream"):
                        yield await self._non_stream_responses_via_sdk(messages, tools)
                        return
                    instructions_parts: List[str] = []
                    input_items: List[Dict[str, Any]] = []
                    for m in messages:
                        if m.role == "system" and m.content:
                            instructions_parts.append(m.content)
                            continue
                        # For streaming, we only support simple text/image union sufficient for deltas.
                        if m.images:
                            parts: List[Dict[str, Any]] = []
                            if m.content:
                                parts.append({"type": "input_text", "text": m.content})
                            for p in (m.images or []):
                                data_url = self._path_to_data_url(p)
                                if data_url:
                                    parts.append({"type": "input_image", "image_url": data_url})
                            input_items.append({"role": m.role, "content": parts})
                        else:
                            input_items.append({"role": m.role, "content": m.content})
                    stream_kwargs: Dict[str, Any] = {
                        "model": (model_override or self.config.model),
                        "input": input_items,
                    }
                    tools_json = self._responses_tools_payload(tools)
                    if tools_json:
                        stream_kwargs["tools"] = tools_json
                        stream_kwargs["tool_choice"] = "auto"
                    if instructions_parts:
                        stream_kwargs["instructions"] = "\n\n".join(instructions_parts)
                    async with self._sdk.responses.stream(  # type: ignore[attr-defined]
                        **stream_kwargs
                    ) as stream:
                        content_buffer = ""
                        async for event in stream:
                            et = getattr(event, "type", None)
                            if isinstance(et, str) and "output_text.delta" in et:
                                delta = getattr(event, "delta", None) or getattr(event, "output_text", None)
                                if isinstance(delta, str) and delta:
                                    content_buffer += delta
                                    yield LLMResponse(content=content_buffer)
                        # Best-effort final response emission
                        try:
                            final = getattr(stream, "get_final_response", None)
                            if callable(final):
                                fr = await final()
                                text = getattr(fr, "output_text", None)
                                if isinstance(text, str) and text and text != content_buffer:
                                    yield LLMResponse(content=text)
                        except Exception:
                            pass
                except Exception as e:
                    logger.error("OpenAI Responses (SDK stream) error", error=str(e))
                    return
            # In an async generator function, we cannot `return` a value. Forward the
            # inner generator explicitly.
            async for _ev in _gen():
                yield _ev
            return
        model = model_override or self.config.model
        instructions_parts: List[str] = []
        input_items: List[Dict[str, Any]] = []
        for m in messages:
            if m.role == "system" and m.content:
                instructions_parts.append(m.content)
                continue
            if m.images:
                parts: List[Dict[str, Any]] = []
                if m.content:
                    parts.append({"type": "input_text", "text": m.content})
                for p in (m.images or []):
                    data_url = self._path_to_data_url(p)
                    if data_url:
                        parts.append({"type": "input_image", "image_url": data_url})
                input_items.append({"role": m.role, "content": parts})
            else:
                input_items.append({"role": m.role, "content": m.content})
        payload: Dict[str, Any] = {
            "model": model,
            "input": input_items,
            "stream": True,
        }
        if instructions_parts:
            payload["instructions"] = "\n\n".join(instructions_parts)
        tool_defs = self._responses_tools_payload(tools)
        if tool_defs:
            payload["tools"] = tool_defs
            payload["tool_choice"] = "auto"
        try:
            cm, response = await self._enter_stream_with_retries(
                f"{self.base_url}/responses",
                json=payload,
                headers=self._responses_headers(),
            )
            response.raise_for_status()

            content_buffer = ""
            # parse SSE: lines may include 'event: ...' and 'data: ...'
            current_event = None
            # Buffer tool calls by id
            tool_calls_buffer: Dict[str, Dict[str, Any]] = {}
            try:
                async for raw_line in response.aiter_lines():
                    line = (raw_line or "").strip()
                    if not line:
                        continue
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        continue
                    if line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            obj = json.loads(data_str)
                        except Exception:
                            continue
                        ev = current_event or obj.get("type")
                        # output text deltas
                        if ev and ("output_text.delta" in ev or ev.endswith("output_text.delta")):
                            delta = obj.get("delta") or obj.get("text") or obj.get("output_text") or ""
                            if isinstance(delta, dict):
                                delta = delta.get("content", "")
                            content_buffer += delta or ""
                            yield LLMResponse(content=content_buffer)
                        # reasoning deltas
                        elif ev and ("reasoning.delta" in ev or ev.endswith("reasoning.delta")):
                            reason = obj.get("delta") or obj.get("reasoning") or obj.get("content") or ""
                            if isinstance(reason, dict):
                                reason = reason.get("content", "")
                            if reason:
                                yield LLMResponse(content=content_buffer, reasoning_raw_delta=reason)
                        # tool result deltas surfaced separately
                        elif ev and (
                            "tool_result.delta" in ev or ev.endswith("tool_result.delta") or
                            "output_tool_result.delta" in ev or ev.endswith("output_tool_result.delta") or
                            "tool_output.delta" in ev or ev.endswith("tool_output.delta")
                        ):
                            part = obj.get("delta") or obj.get("content") or obj.get("text") or ""
                            if isinstance(part, dict):
                                part = part.get("content", "")
                            yield LLMResponse(content=content_buffer, tool_result_delta=part or "")
                        # tool call deltas (heuristics)
                        elif ev and ("tool_call.delta" in ev or ev.endswith("tool_call.delta") or "output_tool_call.delta" in ev):
                            call = obj.get("delta") or obj.get("tool_call") or obj
                            call_id = call.get("id") or call.get("tool_call_id") or "0"
                            buf = tool_calls_buffer.setdefault(call_id, {"id": call_id, "name": "", "arguments": ""})
                            # name may appear
                            name = call.get("name") or call.get("function", {}).get("name")
                            if name:
                                buf["name"] = name
                            args_part = None
                            if isinstance(call.get("arguments"), str):
                                args_part = call.get("arguments")
                            elif isinstance(call.get("function"), dict) and isinstance(call["function"].get("arguments"), str):
                                args_part = call["function"]["arguments"]
                            if args_part:
                                buf["arguments"] += args_part
                        elif ev and ("tool_call.completed" in ev or ev.endswith("tool_call.completed") or "output_tool_call.completed" in ev or ev.endswith("output_tool_call.completed")):
                            call = obj.get("tool_call") or obj
                            call_id = (call.get("id") or call.get("tool_call_id") or "0")
                            buf = tool_calls_buffer.get(call_id)
                            if buf and buf.get("name"):
                                try:
                                    args_obj = json.loads(buf.get("arguments") or "{}")
                                except Exception:
                                    args_obj = {}
                                yield LLMResponse(
                                    content=content_buffer,
                                    tool_calls=[LLMToolCall(id=buf["id"], name=buf["name"], arguments=args_obj)],
                                )
                                # drop consumed buffer
                                tool_calls_buffer.pop(call_id, None)
                        # completed
                        elif ev and ("completed" in ev or ev.endswith("completed")):
                            break
                        else:
                            # ignore other events
                            pass
            finally:
                await cm.__aexit__(None, None, None)
        except Exception as e:
            logger.error("OpenAI Responses (stream) error", error=str(e))
            # Stop the async generator on error
            return
    
    async def _non_stream_chat(self, payload: Dict) -> LLMResponse:
        """Non-streaming chat completion"""
        try:
            response = await self._post_with_retries(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
            )
            data = response.json()
            
            choice = data["choices"][0]
            message = choice["message"]
            
            # Parse tool calls
            tool_calls = []
            if "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    tool_calls.append(LLMToolCall(
                        id=tool_call["id"],
                        name=tool_call["function"]["name"],
                        arguments=json.loads(tool_call["function"]["arguments"])
                    ))
            
            # Reasoning (targeted parser)
            reasoning_raw = None
            # known vendor/proxy extensions sometimes attach `reasoning` or `reasoning_content`
            if isinstance(message, dict):
                if isinstance(message.get("reasoning"), str):
                    reasoning_raw = message["reasoning"]
                elif isinstance(message.get("reasoning_content"), str):
                    reasoning_raw = message["reasoning_content"]
                elif isinstance(message.get("x_reasoning"), str):
                    reasoning_raw = message["x_reasoning"]
                # some APIs place reasoning tokens as an array under `reasoning`
                elif isinstance(message.get("reasoning"), list):
                    try:
                        reasoning_raw = "".join([x for x in message["reasoning"] if isinstance(x, str)])
                    except Exception:
                        pass
            
            return LLMResponse(
                content=message.get("content", ""),
                tool_calls=tool_calls,
                usage=data.get("usage"),
                finish_reason=choice.get("finish_reason"),
                reasoning_raw_delta=reasoning_raw
            )
            
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise
    
    async def _stream_chat(self, payload: Dict) -> AsyncIterator[LLMResponse]:
        """Streaming chat completion"""
        try:
            cm, response = await self._enter_stream_with_retries(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
                
            content_buffer = ""
            tool_calls_buffer = {}
            reasoning_buffer = ""
            
            try:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                    
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"]
                        
                        # Handle content
                        if "content" in delta:
                            content_buffer += delta["content"] or ""
                            yield LLMResponse(content=content_buffer)
                        
                        # Heuristic handling for reasoning content when present
                        # Some providers may emit `reasoning` or `reasoning_content` keys
                        # in either the choice-level object or the delta.
                        raw_reason = None
                        if isinstance(delta, dict):
                            if "reasoning" in delta and isinstance(delta["reasoning"], str):
                                raw_reason = delta["reasoning"]
                            elif "reasoning_content" in delta and isinstance(delta["reasoning_content"], str):
                                raw_reason = delta["reasoning_content"]
                        if raw_reason:
                            reasoning_buffer += raw_reason
                            yield LLMResponse(content=content_buffer, reasoning_raw_delta=raw_reason)
                        
                        # Handle tool calls
                        if "tool_calls" in delta:
                            for tool_call_delta in delta["tool_calls"]:
                                index = tool_call_delta.get("index", 0)
                                if index not in tool_calls_buffer:
                                    tool_calls_buffer[index] = {
                                        "id": "",
                                        "name": "",
                                        "arguments": ""
                                    }
                                
                                if "id" in tool_call_delta.get("function", {}):
                                    tool_calls_buffer[index]["id"] = tool_call_delta["function"]["id"]
                                
                                if "name" in tool_call_delta.get("function", {}):
                                    tool_calls_buffer[index]["name"] = tool_call_delta["function"]["name"]
                                
                                if "arguments" in tool_call_delta.get("function", {}):
                                    tool_calls_buffer[index]["arguments"] += tool_call_delta["function"]["arguments"]
                                
                                # Yield complete tool calls
                                if tool_calls_buffer[index]["id"] and tool_calls_buffer[index]["name"]:
                                    try:
                                        arguments = json.loads(tool_calls_buffer[index]["arguments"])
                                        yield LLMResponse(
                                            content=content_buffer,
                                            tool_calls=[LLMToolCall(
                                                id=tool_calls_buffer[index]["id"],
                                                name=tool_calls_buffer[index]["name"],
                                                arguments=arguments
                                            )]
                                        )
                                    except json.JSONDecodeError:
                                        pass  # Incomplete JSON
                    
                    except json.JSONDecodeError:
                        continue
            finally:
                await cm.__aexit__(None, None, None)
        except Exception as e:
            logger.error("OpenAI streaming error", error=str(e))
            raise
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI"""
        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                json={
                    "model": "text-embedding-ada-002",
                    "input": text
                },
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
            
        except Exception as e:
            logger.error("OpenAI embeddings error", error=str(e))
            raise


class OllamaClient(LLMClient):
    """Ollama API client for local models"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncIterator[LLMResponse]]:
        """Send chat messages to Ollama"""
        
        # Convert messages to Ollama format (support images as base64)
        ollama_messages = []
        for msg in messages:
            m: Dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.images:
                import base64
                imgs: List[str] = []
                for p in msg.images:
                    try:
                        with open(p, "rb") as f:
                            imgs.append(base64.b64encode(f.read()).decode("ascii"))
                    except Exception:
                        continue
                if imgs:
                    m["images"] = imgs
            ollama_messages.append(m)
        
        # Prepare request payload
        payload = {
            "model": self.config.model,
            "messages": ollama_messages,
            "stream": stream,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        if stream:
            return self._stream_chat(payload)
        else:
            return await self._non_stream_chat(payload)
    
    async def _non_stream_chat(self, payload: Dict) -> LLMResponse:
        """Non-streaming chat completion"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                usage=data.get("usage")
            )
            
        except Exception as e:
            logger.error("Ollama API error", error=str(e))
            raise
    
    async def _stream_chat(self, payload: Dict) -> AsyncIterator[LLMResponse]:
        """Streaming chat completion"""
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                
                content_buffer = ""
                reasoning_buffer = ""
                
                async for line in response.aiter_lines():
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            content_buffer += data["message"]["content"] or ""
                            yield LLMResponse(content=content_buffer)
                        # No standard reasoning stream in Ollama; keep hook here in case of vendor extensions
                        if "reasoning" in data and isinstance(data["reasoning"], str):
                            reasoning_buffer += data["reasoning"]
                            yield LLMResponse(content=content_buffer, reasoning_raw_delta=data["reasoning"])
                        
                        if data.get("done"):
                            break
                    
                    except json.JSONDecodeError:
                        continue
            
        except Exception as e:
            logger.error("Ollama streaming error", error=str(e))
            raise
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings using Ollama"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.config.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
            
        except Exception as e:
            logger.error("Ollama embeddings error", error=str(e))
            raise


class LLMManager:
    """Manages multiple LLM clients and provides unified interface"""
    
    def __init__(self):
        self.clients: Dict[str, LLMClient] = {}
        self.default_client: Optional[str] = None
    
    def add_client(self, name: str, client: LLMClient, is_default: bool = False) -> None:
        """Add an LLM client"""
        self.clients[name] = client
        if is_default or self.default_client is None:
            self.default_client = name
    
    def get_client(self, name: Optional[str] = None) -> LLMClient:
        """Get an LLM client by name"""
        if name is None:
            name = self.default_client
        
        if name not in self.clients:
            raise ValueError(f"LLM client '{name}' not found")
        
        return self.clients[name]
    
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        client_name: Optional[str] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncIterator[LLMResponse]]:
        """Send chat messages using specified or default client"""
        client = self.get_client(client_name)
        return await client.chat(messages, tools, stream)
    
    async def close_all(self) -> None:
        """Close all LLM clients"""
        for client in self.clients.values():
            await client.close()


def create_llm_client(config: LLMConfig) -> LLMClient:
    """Factory function to create LLM client based on provider"""
    if config.provider == LLMProvider.OPENAI:
        return OpenAIClient(config)
    elif config.provider == LLMProvider.OLLAMA:
        return OllamaClient(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


# Convenience functions
async def chat_with_llm(
    messages: List[Union[str, Dict, LLMMessage]],
    config: LLMConfig,
    tools: Optional[List[LLMTool]] = None,
    stream: bool = False
) -> Union[LLMResponse, AsyncIterator[LLMResponse]]:
    """Convenience function for single LLM chat"""
    # Convert various message formats to LLMMessage
    normalized_messages = []
    for msg in messages:
        if isinstance(msg, str):
            normalized_messages.append(LLMMessage(role="user", content=msg))
        elif isinstance(msg, dict):
            normalized_messages.append(LLMMessage(**msg))
        else:
            normalized_messages.append(msg)
    
    client = create_llm_client(config)
    try:
        return await client.chat(normalized_messages, tools, stream)
    finally:
        await client.close()
