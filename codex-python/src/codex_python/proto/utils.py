"""
Protocol buffer utilities and helpers for Codex Python
"""

import asyncio
import structlog
from typing import Any, Dict, List, Optional, Union, AsyncIterator
from dataclasses import asdict

import proto.codex_pb2 as codex_proto
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.timestamp_pb2 import Timestamp

logger = structlog.get_logger(__name__)


class ProtobufConverter:
    """Converts between Python objects and Protocol Buffer messages"""
    
    @staticmethod
    def dict_to_value(data: Any) -> codex_proto.Value:
        """Convert Python dict to protobuf Value"""
        if data is None:
            return codex_proto.Value(null_value=codex_proto.NullValue.NULL_VALUE)
        elif isinstance(data, str):
            return codex_proto.Value(string_value=data)
        elif isinstance(data, int):
            return codex_proto.Value(int_value=data)
        elif isinstance(data, float):
            return codex_proto.Value(double_value=data)
        elif isinstance(data, bool):
            return codex_proto.Value(bool_value=data)
        elif isinstance(data, list):
            list_value = codex_proto.ValueList()
            for item in data:
                list_value.values.append(ProtobufConverter.dict_to_value(item))
            return codex_proto.Value(list_value=list_value)
        elif isinstance(data, dict):
            map_value = codex_proto.ValueMap()
            for key, value in data.items():
                map_value.values[key] = ProtobufConverter.dict_to_value(value)
            return codex_proto.Value(map_value=map_value)
        elif isinstance(data, bytes):
            return codex_proto.Value(bytes_value=data)
        else:
            raise ValueError(f"Unsupported type: {type(data)}")
    
    @staticmethod
    def value_to_dict(value: codex_proto.Value) -> Any:
        """Convert protobuf Value to Python dict"""
        if value.HasField("null_value"):
            return None
        elif value.HasField("string_value"):
            return value.string_value
        elif value.HasField("int_value"):
            return value.int_value
        elif value.HasField("double_value"):
            return value.double_value
        elif value.HasField("bool_value"):
            return value.bool_value
        elif value.HasField("list_value"):
            return [ProtobufConverter.value_to_dict(v) for v in value.list_value.values]
        elif value.HasField("map_value"):
            return {
                key: ProtobufConverter.value_to_dict(v)
                for key, v in value.map_value.values.items()
            }
        elif value.HasField("bytes_value"):
            return value.bytes_value
        else:
            raise ValueError(f"Unknown value type: {value}")
    
    @staticmethod
    def tool_to_proto(tool_info) -> codex_proto.Tool:
        """Convert tool info to protobuf Tool message"""
        tool_proto = codex_proto.Tool(
            name=tool_info.name,
            description=tool_info.description,
            tags=list(tool_info.tags),
            category=tool_info.category or "",
            permission=ProtobufConverter.permission_to_proto(tool_info.permission)
        )
        
        # Convert input schema
        if hasattr(tool_info, 'input_schema') and tool_info.input_schema:
            tool_proto.input_schema.CopyFrom(ProtobufConverter.schema_to_proto(tool_info.input_schema))
        
        return tool_proto
    
    @staticmethod
    def proto_to_tool(tool_proto: codex_proto.Tool) -> Dict[str, Any]:
        """Convert protobuf Tool to Python dict"""
        return {
            "name": tool_proto.name,
            "description": tool_proto.description,
            "input_schema": ProtobufConverter.proto_to_schema(tool_proto.input_schema),
            "tags": list(tool_proto.tags),
            "category": tool_proto.category or None,
            "permission": ProtobufConverter.proto_to_permission(tool_proto.permission)
        }
    
    @staticmethod
    def schema_to_proto(schema: Dict[str, Any]) -> codex_proto.Schema:
        """Convert Python schema dict to protobuf Schema"""
        schema_proto = codex_proto.Schema(
            type=schema.get("type", "object"),
            description=schema.get("description", "")
        )
        
        # Add properties
        if "properties" in schema:
            for key, prop_schema in schema["properties"].items():
                schema_proto.properties[key].CopyFrom(ProtobufConverter.schema_to_proto(prop_schema))
        
        # Add required fields
        if "required" in schema:
            schema_proto.required.extend(schema["required"])
        
        # Add default value
        if "default" in schema:
            schema_proto.default_value.CopyFrom(ProtobufConverter.dict_to_value(schema["default"]))
        
        return schema_proto
    
    @staticmethod
    def proto_to_schema(schema_proto: codex_proto.Schema) -> Dict[str, Any]:
        """Convert protobuf Schema to Python dict"""
        schema = {
            "type": schema_proto.type,
            "description": schema_proto.description
        }
        
        # Add properties
        if schema_proto.properties:
            schema["properties"] = {
                key: ProtobufConverter.proto_to_schema(prop_schema)
                for key, prop_schema in schema_proto.properties.items()
            }
        
        # Add required fields
        if schema_proto.required:
            schema["required"] = list(schema_proto.required)
        
        # Add default value
        if schema_proto.HasField("default_value"):
            schema["default"] = ProtobufConverter.value_to_dict(schema_proto.default_value)
        
        return schema
    
    @staticmethod
    def permission_to_proto(permission) -> codex_proto.ToolPermission:
        """Convert ToolPermission to protobuf enum"""
        mapping = {
            "allow": codex_proto.TOOL_PERMISSION_ALLOW,
            "block": codex_proto.TOOL_PERMISSION_BLOCK,
            "sandbox": codex_proto.TOOL_PERMISSION_SANDBOX,
        }
        return mapping.get(getattr(permission, 'value', permission), codex_proto.TOOL_PERMISSION_UNSPECIFIED)
    
    @staticmethod
    def proto_to_permission(permission_proto: codex_proto.ToolPermission) -> str:
        """Convert protobuf enum to ToolPermission string"""
        mapping = {
            codex_proto.TOOL_PERMISSION_ALLOW: "allow",
            codex_proto.TOOL_PERMISSION_BLOCK: "block",
            codex_proto.TOOL_PERMISSION_SANDBOX: "sandbox",
        }
        return mapping.get(permission_proto, "unspecified")
    
    @staticmethod
    def server_config_to_proto(config) -> codex_proto.ServerConfig:
        """Convert server config to protobuf"""
        return codex_proto.ServerConfig(
            name=config.name,
            command=config.command,
            args=list(config.args),
            transport=config.transport,
            url=config.url or "",
            env=dict(config.env),
            timeout_s=int(config.timeout)
        )
    
    @staticmethod
    def proto_to_server_config(config_proto: codex_proto.ServerConfig) -> Dict[str, Any]:
        """Convert protobuf server config to Python dict"""
        return {
            "name": config_proto.name,
            "command": config_proto.command,
            "args": list(config_proto.args),
            "transport": config_proto.transport,
            "url": config_proto.url or None,
            "env": dict(config_proto.env),
            "timeout": float(config_proto.timeout_s)
        }
    
    @staticmethod
    def create_message(
        message_type: str,
        payload: Optional[Any] = None,
        message_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> codex_proto.Message:
        """Create a protobuf message"""
        msg = codex_proto.Message()
        
        if message_id:
            msg.id = message_id
        else:
            import uuid
            msg.id = str(uuid.uuid4())
        
        msg.type = ProtobufConverter.message_type_to_proto(message_type)
        
        # Add timestamp
        timestamp = Timestamp()
        timestamp.GetCurrentTime()
        msg.timestamp.CopyFrom(timestamp)
        
        # Add metadata
        if metadata:
            msg.metadata.update(metadata)
        
        # Add payload
        if payload:
            if message_type == "request":
                if isinstance(payload, dict):
                    msg.request.params.update({
                        k: ProtobufConverter.dict_to_value(v) for k, v in payload.items()
                    })
            elif message_type == "response":
                if hasattr(payload, 'result'):
                    msg.response.result.CopyFrom(ProtobufConverter.dict_to_value(payload.result))
                msg.response.success = getattr(payload, 'success', True)
            elif message_type == "error":
                msg.error.code = getattr(payload, 'code', 'UNKNOWN_ERROR')
                msg.error.message = getattr(payload, 'message', 'Unknown error')
            elif message_type == "notification":
                msg.notification.event = getattr(payload, 'event', 'unknown')
                if hasattr(payload, 'data'):
                    msg.notification.data.update({
                        k: ProtobufConverter.dict_to_value(v) for k, v in payload.data.items()
                    })
        
        return msg
    
    @staticmethod
    def message_type_to_proto(message_type: str) -> codex_proto.MessageType:
        """Convert string message type to protobuf enum"""
        mapping = {
            "request": codex_proto.MESSAGE_TYPE_REQUEST,
            "response": codex_proto.MESSAGE_TYPE_RESPONSE,
            "error": codex_proto.MESSAGE_TYPE_ERROR,
            "notification": codex_proto.MESSAGE_TYPE_NOTIFICATION,
        }
        return mapping.get(message_type, codex_proto.MESSAGE_TYPE_UNSPECIFIED)
    
    @staticmethod
    def proto_to_message_type(message_type_proto: codex_proto.MessageType) -> str:
        """Convert protobuf enum to string message type"""
        mapping = {
            codex_proto.MESSAGE_TYPE_REQUEST: "request",
            codex_proto.MESSAGE_TYPE_RESPONSE: "response",
            codex_proto.MESSAGE_TYPE_ERROR: "error",
            codex_proto.MESSAGE_TYPE_NOTIFICATION: "notification",
        }
        return mapping.get(message_type_proto, "unspecified")


class ProtobufStreamHandler:
    """Handles streaming protocol buffer messages"""
    
    def __init__(self):
        self._streams: Dict[str, asyncio.Queue] = {}
        self._stream_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_stream(self, stream_id: str) -> asyncio.Queue:
        """Create a new stream"""
        if stream_id in self._streams:
            raise ValueError(f"Stream {stream_id} already exists")
        
        queue = asyncio.Queue()
        self._streams[stream_id] = queue
        return queue
    
    async def get_stream(self, stream_id: str) -> Optional[asyncio.Queue]:
        """Get an existing stream"""
        return self._streams.get(stream_id)
    
    async def send_to_stream(self, stream_id: str, response: codex_proto.StreamResponse) -> None:
        """Send a response to a stream"""
        if stream_id not in self._streams:
            logger.warning("Stream not found", stream_id=stream_id)
            return
        
        queue = self._streams[stream_id]
        await queue.put(response)
    
    async def close_stream(self, stream_id: str) -> None:
        """Close a stream"""
        if stream_id in self._streams:
            # Send completion status
            completion = codex_proto.StreamResponse(
                stream_id=stream_id,
                status=codex_proto.StreamStatus(
                    state=codex_proto.STREAM_STATE_COMPLETED,
                    message="Stream completed"
                )
            )
            await self.send_to_stream(stream_id, completion)
            
            # Clean up
            del self._streams[stream_id]
            
            if stream_id in self._stream_tasks:
                task = self._stream_tasks[stream_id]
                task.cancel()
                del self._stream_tasks[stream_id]
    
    async def stream_tool_results(
        self,
        stream_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        tool_func
    ) -> AsyncIterator[codex_proto.StreamResponse]:
        """Stream tool execution results"""
        try:
            queue = await self.create_stream(stream_id)
            
            # Start tool execution in background
            async def execute_tool():
                try:
                    # Execute the tool
                    result = await tool_func(tool_name, arguments)
                    
                    # Stream results
                    if hasattr(result, 'content'):
                        for content in result.content:
                            response = codex_proto.StreamResponse(
                                stream_id=stream_id,
                                content=ProtobufConverter.content_to_proto(content)
                            )
                            await queue.put(response)
                    
                    # Send completion
                    completion = codex_proto.StreamResponse(
                        stream_id=stream_id,
                        status=codex_proto.StreamStatus(
                            state=codex_proto.STREAM_STATE_COMPLETED,
                            message="Tool execution completed"
                        )
                    )
                    await queue.put(completion)
                    
                except Exception as e:
                    # Send error
                    error_response = codex_proto.StreamResponse(
                        stream_id=stream_id,
                        error=codex_proto.StreamError(
                            code="EXECUTION_ERROR",
                            message=str(e)
                        )
                    )
                    await queue.put(error_response)
                finally:
                    await self.close_stream(stream_id)
            
            task = asyncio.create_task(execute_tool())
            self._stream_tasks[stream_id] = task
            
            # Yield responses from queue
            while True:
                response = await queue.get()
                yield response
                
                # Check if stream is completed
                if response.HasField("status"):
                    if response.status.state in [
                        codex_proto.STREAM_STATE_COMPLETED,
                        codex_proto.STREAM_STATE_ERROR,
                        codex_proto.STREAM_STATE_CANCELLED
                    ]:
                        break
                
                if response.HasField("error"):
                    break
        
        except Exception as e:
            logger.error("Error in stream_tool_results", error=str(e))
            yield codex_proto.StreamResponse(
                stream_id=stream_id,
                error=codex_proto.StreamError(
                    code="STREAM_ERROR",
                    message=str(e)
                )
            )
    
    @staticmethod
    def content_to_proto(content) -> codex_proto.Content:
        """Convert content to protobuf"""
        content_proto = codex_proto.Content()
        
        if hasattr(content, 'text') and content.text:
            content_proto.type = codex_proto.CONTENT_TYPE_TEXT
            content_proto.text.text = content.text
            content_proto.text.mime_type = getattr(content, 'mime_type', 'text/plain')
        elif hasattr(content, 'data') and content.data:
            content_proto.type = codex_proto.CONTENT_TYPE_IMAGE
            content_proto.image.data = content.data
            content_proto.image.mime_type = getattr(content, 'mime_type', 'image/png')
        elif hasattr(content, 'uri') and content.uri:
            content_proto.type = codex_proto.CONTENT_TYPE_RESOURCE
            content_proto.resource.uri = content.uri
            content_proto.resource.mime_type = getattr(content, 'mime_type', 'application/octet-stream')
            if hasattr(content, 'data'):
                content_proto.resource.data = content.data
        
        return content_proto