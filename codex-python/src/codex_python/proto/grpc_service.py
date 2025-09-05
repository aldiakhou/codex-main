"""
gRPC service implementation for Codex Python
"""

import asyncio
import structlog
from typing import AsyncIterator, Dict, List, Optional

import grpc
import proto.codex_pb2 as codex_proto
import proto.codex_pb2_grpc as codex_grpc

from ..core.client import CodexClient
from ..core.config import Config
from ..core.orchestrator import CodexOrchestrator
from .utils import ProtobufConverter


logger = structlog.get_logger(__name__)


class CodexGRPCService(codex_grpc.CodexServiceServicer):
    """gRPC service implementation for Codex"""
    
    def __init__(self, client: CodexClient, orchestrator: Optional[CodexOrchestrator] = None):
        self.client = client
        self.converter = ProtobufConverter()
        self._orch = orchestrator
    
    async def ListTools(
        self, 
        request: codex_proto.ListToolsRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.ListToolsResponse:
        """List available tools"""
        try:
            # Convert request parameters
            server_name = request.server_name if request.server_name else None
            category = request.category if request.category else None
            tags = list(request.tags) if request.tags else None
            permission = self.converter.proto_to_permission(request.permission) if request.permission else None
            
            # Get tools from registry
            tools = self.client.tool_registry.list_tools(
                server_name=server_name,
                category=category,
                tags=set(tags) if tags else None,
                permission=permission
            )
            
            # Convert to protobuf
            response = codex_proto.ListToolsResponse()
            for tool_info in tools:
                # Prefer qualified names when exposing via gRPC
                qname = self.client.tool_registry.qualified_name_for(tool_info) or tool_info.name
                # create a shallow copy for name substitution
                tmp = type("_Tmp", (), {})()
                tmp.name = qname
                tmp.description = tool_info.description
                tmp.tags = tool_info.tags
                tmp.category = tool_info.category
                tmp.input_schema = tool_info.input_schema
                tmp.permission = tool_info.permission
                tool_proto = self.converter.tool_to_proto(tmp)
                response.tools.append(tool_proto)
            
            return response
            
        except Exception as e:
            logger.error("Error in ListTools", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    # --- Exec API ---
    async def Exec(
        self,
        request: codex_proto.ExecRequest,
        context: grpc.aio.ServicerContext,
    ) -> codex_proto.ExecResponse:
        try:
            orch = self._orch or CodexOrchestrator(self.client.config)
            await orch.initialize()
            env = dict(request.env)
            res = await orch.execute_command(list(request.command), cwd=request.cwd or None, env=env)
            return codex_proto.ExecResponse(
                success=res.success,
                returncode=int(res.result.get("returncode", 1) if isinstance(res.result, dict) else (0 if res.success else 1)),
                stdout=(res.result.get("stdout", "") if isinstance(res.result, dict) else ""),
                stderr=(res.result.get("stderr", "") if isinstance(res.result, dict) else ""),
            )
        except Exception as e:
            logger.error("Error in Exec", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def ExecStream(
        self,
        request: codex_proto.ExecRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterator[codex_proto.ExecStreamResponse]:
        try:
            orch = self._orch or CodexOrchestrator(self.client.config)
            await orch.initialize()
            env = dict(request.env)
            async for item in orch.execute_command_stream(list(request.command), cwd=request.cwd or None, env=env):
                if item.get("type") == "delta":
                    yield codex_proto.ExecStreamResponse(
                        delta=codex_proto.ExecDelta(
                            stream=item.get("stream", "stdout"),
                            data=item.get("data", b""),
                        )
                    )
                elif item.get("type") == "result":
                    yield codex_proto.ExecStreamResponse(done=codex_proto.ExecDone(returncode=int(item.get("returncode", 1))))
                elif item.get("type") == "error":
                    yield codex_proto.ExecStreamResponse(error=codex_proto.StreamError(code="EXEC_ERROR", message=item.get("message", "error")))
                    break
        except Exception as e:
            logger.error("Error in ExecStream", error=str(e))
            yield codex_proto.ExecStreamResponse(error=codex_proto.StreamError(code="EXEC_ERROR", message=str(e)))

    # --- Patch API ---
    async def ApplyPatch(
        self,
        request: codex_proto.ApplyPatchRequest,
        context: grpc.aio.ServicerContext,
    ) -> codex_proto.ApplyPatchResponse:
        try:
            orch = self._orch or CodexOrchestrator(self.client.config)
            await orch.initialize()
            res = await orch.apply_patch(request.patch_text, root_path=request.root_path or None)
            return codex_proto.ApplyPatchResponse(success=res.success, message=res.error or "")
        except Exception as e:
            logger.error("Error in ApplyPatch", error=str(e))
            return codex_proto.ApplyPatchResponse(success=False, message=str(e))
    
    async def CallTool(
        self, 
        request: codex_proto.ToolCallRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.ToolCallResponse:
        """Call a tool"""
        try:
            # Convert arguments
            arguments = {
                key: self.converter.value_to_dict(value)
                for key, value in request.arguments.items()
            }
            
            # Call tool
            result = await self.client.call_tool(
                tool_name=request.tool_name,
                arguments=arguments,
                server_name=request.session_id if request.session_id else None
            )
            
            # Convert response
            response = codex_proto.ToolCallResponse(
                tool_name=request.tool_name,
                success=result.isError if hasattr(result, 'isError') else True
            )
            
            # Add content
            if hasattr(result, 'content'):
                for content in result.content:
                    content_proto = self.converter.content_to_proto(content)
                    response.content.append(content_proto)
            
            # Add error message if present
            if hasattr(result, 'isError') and result.isError:
                response.error_message = "Tool execution failed"
            
            return response
            
        except Exception as e:
            logger.error("Error in CallTool", tool=request.tool_name, error=str(e))
            return codex_proto.ToolCallResponse(
                tool_name=request.tool_name,
                success=False,
                error_message=str(e)
            )
    
    async def StreamTool(
        self, 
        request: codex_proto.StreamToolRequest, 
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[codex_proto.StreamResponse]:
        """Stream tool execution results"""
        try:
            for stream_request in request.requests:
                # Convert arguments
                arguments = {
                    key: self.converter.value_to_dict(value)
                    for key, value in stream_request.arguments.items()
                }
                
                # Stream results
                async for response in self.client.stream_tool_call(
                    tool_name=stream_request.tool_name,
                    arguments=arguments,
                    server_name=stream_request.session_id if stream_request.session_id else None
                ):
                    # Convert to protobuf
                    response_proto = codex_proto.StreamResponse(
                        stream_id=stream_request.stream_id,
                        content=self.converter.content_to_proto(response)
                    )
                    yield response_proto
            
        except Exception as e:
            logger.error("Error in StreamTool", error=str(e))
            # Yield error response
            error_response = codex_proto.StreamResponse(
                stream_id=request.requests[0].stream_id if request.requests else "unknown",
                error=codex_proto.StreamError(
                    code="STREAM_ERROR",
                    message=str(e)
                )
            )
            yield error_response
    
    async def ListServers(
        self, 
        request: codex_proto.ListServersRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.ListServersResponse:
        """List configured servers"""
        try:
            response = codex_proto.ListServersResponse()
            
            # Add server configurations
            for server_config in self.client.config.servers.values():
                server_proto = self.converter.server_config_to_proto(server_config)
                response.servers.append(server_proto)
            
            # Add server statuses if requested
            if request.include_status:
                servers_info = await self.client.get_all_servers_info()
                for server_name, info in servers_info.items():
                    status_proto = codex_proto.ServerStatus(
                        name=server_name,
                        state=codex_proto.SERVER_STATE_CONNECTED if info.get('connected') else codex_proto.SERVER_STATE_DISCONNECTED,
                        error_message=info.get('error', ''),
                        tool_count=info.get('tool_count', 0)
                    )
                    response.statuses.append(status_proto)
            
            return response
            
        except Exception as e:
            logger.error("Error in ListServers", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def GetServerStatus(
        self, 
        request: codex_proto.GetServerStatusRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.ServerStatus:
        """Get status of a specific server"""
        try:
            server_name = request.server_name
            info = await self.client.get_server_info(server_name)
            
            return codex_proto.ServerStatus(
                name=server_name,
                state=codex_proto.SERVER_STATE_CONNECTED if info.get('connected') else codex_proto.SERVER_STATE_DISCONNECTED,
                error_message=info.get('error', ''),
                tool_count=info.get('tool_count', 0)
            )
            
        except Exception as e:
            logger.error("Error in GetServerStatus", server=request.server_name, error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def AddServer(
        self, 
        request: codex_proto.AddServerRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.AddServerResponse:
        """Add a new server configuration"""
        try:
            # Convert protobuf to config
            config_dict = self.converter.proto_to_server_config(request.config)
            
            # Create server config object
            from ..core.config import ServerConfig
            server_config = ServerConfig(**config_dict)
            
            # Add server
            await self.client.connection_manager.add_server(
                server_config.name, 
                server_config
            )
            
            return codex_proto.AddServerResponse(
                success=True,
                message=f"Server {server_config.name} added successfully"
            )
            
        except Exception as e:
            logger.error("Error in AddServer", error=str(e))
            return codex_proto.AddServerResponse(
                success=False,
                message=str(e)
            )
    
    async def RemoveServer(
        self, 
        request: codex_proto.RemoveServerRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.RemoveServerResponse:
        """Remove a server configuration"""
        try:
            server_name = request.server_name
            
            # Remove server
            await self.client.connection_manager.remove_server(server_name)
            
            return codex_proto.RemoveServerResponse(
                success=True,
                message=f"Server {server_name} removed successfully"
            )
            
        except Exception as e:
            logger.error("Error in RemoveServer", server=request.server_name, error=str(e))
            return codex_proto.RemoveServerResponse(
                success=False,
                message=str(e)
            )
    
    async def HealthCheck(
        self, 
        request: codex_proto.HealthCheckRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.HealthCheckResponse:
        """Perform health check"""
        try:
            health_info = await self.client.health_check()
            
            # Convert overall health
            overall_health = codex_proto.OverallHealth(
                status=self.converter.health_status_to_proto(health_info['status']),
                message="Health check completed"
            )
            
            response = codex_proto.HealthCheckResponse(overall=overall_health)
            
            # Add server health if requested
            if request.include_servers:
                for server_name, server_health in health_info.get('servers', {}).items():
                    server_health_proto = codex_proto.ServerHealth(
                        server_name=server_name,
                        status=self.converter.health_status_to_proto(server_health.get('status', 'unhealthy')),
                        message=server_health.get('error', ''),
                        tool_count=server_health.get('tool_count', 0)
                    )
                    response.servers.append(server_health_proto)
            
            return response
            
        except Exception as e:
            logger.error("Error in HealthCheck", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def WatchHealth(
        self, 
        request: codex_proto.WatchHealthRequest, 
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[codex_proto.HealthCheckResponse]:
        """Stream health check updates"""
        try:
            interval = request.interval_s if request.interval_s else 30
            
            while True:
                # Perform health check
                health_info = await self.client.health_check()
                
                # Convert to protobuf
                overall_health = codex_proto.OverallHealth(
                    status=self.converter.health_status_to_proto(health_info['status']),
                    message="Health check completed"
                )
                
                response = codex_proto.HealthCheckResponse(overall=overall_health)
                
                # Add server health if requested
                if request.include_servers:
                    for server_name, server_health in health_info.get('servers', {}).items():
                        server_health_proto = codex_proto.ServerHealth(
                            server_name=server_name,
                            status=self.converter.health_status_to_proto(server_health.get('status', 'unhealthy')),
                            message=server_health.get('error', ''),
                            tool_count=server_health.get('tool_count', 0)
                        )
                        response.servers.append(server_health_proto)
                
                yield response
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error("Error in WatchHealth", error=str(e))
            yield codex_proto.HealthCheckResponse(
                overall=codex_proto.OverallHealth(
                    status=codex_proto.HEALTH_STATUS_UNHEALTHY,
                    message=str(e)
                )
            )
    
    async def GetConfig(
        self, 
        request: codex_proto.GetConfigRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.GetConfigResponse:
        """Get current configuration"""
        try:
            config_dict = self.client.config.to_dict()
            
            # Remove sensitive information if requested
            if not request.include_sensitive:
                if 'auth' in config_dict:
                    auth = config_dict['auth']
                    if auth.get('client_secret'):
                        auth['client_secret'] = '***REDACTED***'
                    if auth.get('bearer_token'):
                        auth['bearer_token'] = '***REDACTED***'
            
            # Convert to protobuf
            config_proto = codex_proto.GetConfigResponse()
            for key, value in config_dict.items():
                config_proto.config[key] = self.converter.dict_to_value(value)
            
            return config_proto
            
        except Exception as e:
            logger.error("Error in GetConfig", error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def UpdateConfig(
        self, 
        request: codex_proto.UpdateConfigRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.UpdateConfigResponse:
        """Update configuration"""
        try:
            # Convert updates to dict
            updates = {
                key: self.converter.value_to_dict(value)
                for key, value in request.updates.items()
            }
            
            # Apply updates (this is a simplified implementation)
            # In a real implementation, you'd want more sophisticated config merging
            current_config = self.client.config.to_dict()
            current_config.update(updates)
            
            # Create new config
            new_config = Config.from_dict(current_config)
            
            # Update client config
            self.client.config = new_config
            
            # Return updated config
            response = codex_proto.UpdateConfigResponse(
                success=True,
                message="Configuration updated successfully"
            )
            
            for key, value in new_config.to_dict().items():
                response.updated_config[key] = self.converter.dict_to_value(value)
            
            return response
            
        except Exception as e:
            logger.error("Error in UpdateConfig", error=str(e))
            return codex_proto.UpdateConfigResponse(
                success=False,
                message=str(e)
            )
    
    # Placeholder methods for session management
    async def CreateSession(
        self, 
        request: codex_proto.CreateSessionRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.SessionInfo:
        """Create a new session"""
        # Placeholder implementation
        return codex_proto.SessionInfo(
            id="placeholder_session_id",
            server_name=request.server_name,
            state=codex_proto.SESSION_STATE_ACTIVE
        )
    
    async def GetSession(
        self, 
        request: codex_proto.GetSessionRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.SessionInfo:
        """Get session information"""
        # Placeholder implementation
        return codex_proto.SessionInfo(
            id=request.session_id,
            state=codex_proto.SESSION_STATE_ACTIVE
        )
    
    async def ListSessions(
        self, 
        request: codex_proto.ListSessionsRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.ListSessionsResponse:
        """List sessions"""
        # Placeholder implementation
        return codex_proto.ListSessionsResponse()
    
    async def CloseSession(
        self, 
        request: codex_proto.CloseSessionRequest, 
        context: grpc.aio.ServicerContext
    ) -> codex_proto.CloseSessionResponse:
        """Close a session"""
        # Placeholder implementation
        return codex_proto.CloseSessionResponse(
            success=True,
            message="Session closed"
        )
    
    def health_status_to_proto(self, status: str) -> codex_proto.HealthStatus:
        """Convert health status string to protobuf enum"""
        mapping = {
            "healthy": codex_proto.HEALTH_STATUS_HEALTHY,
            "degraded": codex_proto.HEALTH_STATUS_DEGRADED,
            "unhealthy": codex_proto.HEALTH_STATUS_UNHEALTHY,
            "not_initialized": codex_proto.HEALTH_STATUS_UNHEALTHY,
        }
        return mapping.get(status, codex_proto.HEALTH_STATUS_UNSPECIFIED)


class CodexGRPCServer:
    """gRPC server for Codex service"""
    
    def __init__(self, client: CodexClient, host: str = "[::]", port: int = 50051, orchestrator: Optional[CodexOrchestrator] = None):
        self.client = client
        self.host = host
        self.port = port
        self.server = None
        self._orch = orchestrator
    
    async def start(self) -> None:
        """Start the gRPC server"""
        self.server = grpc.aio.server()
        
        # Add service
        codex_grpc.add_CodexServiceServicer_to_server(CodexGRPCService(self.client, orchestrator=self._orch), self.server)
        
        # Add port
        listen_addr = f"{self.host}:{self.port}"
        self.server.add_insecure_port(listen_addr)
        
        # Start server
        await self.server.start()
        logger.info("gRPC server started", address=listen_addr)
    
    async def stop(self, grace: float = 1.0) -> None:
        """Stop the gRPC server"""
        if self.server:
            await self.server.stop(grace)
            logger.info("gRPC server stopped")
    
    async def wait_for_termination(self) -> None:
        """Wait for server termination"""
        if self.server:
            await self.server.wait_for_termination()
