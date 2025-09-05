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
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMTool:
    """Tool definition for LLM function calling"""
    name: str
    description: str
    parameters: Dict[str, Any]
    strict: bool = False


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


class OpenAIClient(LLMClient):
    """OpenAI API client"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[LLMTool]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncIterator[LLMResponse]]:
        """Send chat messages to OpenAI"""
        
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.role, "content": msg.content}
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
            return self._stream_chat(payload)
        else:
            return await self._non_stream_chat(payload)
    
    async def _non_stream_chat(self, payload: Dict) -> LLMResponse:
        """Non-streaming chat completion"""
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
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
            
            return LLMResponse(
                content=message.get("content", ""),
                tool_calls=tool_calls,
                usage=data.get("usage"),
                finish_reason=choice.get("finish_reason")
            )
            
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise
    
    async def _stream_chat(self, payload: Dict) -> AsyncIterator[LLMResponse]:
        """Streaming chat completion"""
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers
            ) as response:
                response.raise_for_status()
                
                content_buffer = ""
                tool_calls_buffer = {}
                
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
        
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            if msg.role == "system":
                ollama_messages.append({"role": "system", "content": msg.content})
            elif msg.role == "user":
                ollama_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                ollama_messages.append({"role": "assistant", "content": msg.content})
        
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
                
                async for line in response.aiter_lines():
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            content_buffer += data["message"]["content"] or ""
                            yield LLMResponse(content=content_buffer)
                        
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