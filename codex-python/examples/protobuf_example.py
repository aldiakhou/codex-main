# Example protobuf usage
"""
Example of using protocol buffers with Codex Python
"""

import asyncio
from pathlib import Path

# These would be generated from the .proto files
# from codex_python.proto import codex_pb2, codex_pb2_grpc
# from codex_python.proto.grpc_service import CodexGRPCServer
# from codex_python.proto.utils import ProtobufConverter

from codex_python import CodexClient, Config


async def protobuf_example():
    """Example of protobuf usage"""
    print("=== Protocol Buffers Example ===")
    
    # Create configuration
    config = Config()
    
    # Add a test server
    config.servers["test"] = config.ServerConfig(
        name="test",
        command="echo",
        args=["hello"],
        transport="stdio"
    )
    
    # Create client
    async with CodexClient(config) as client:
        print("Client initialized with protocol buffer support")
        
        # The following would use protobuf if the gRPC service was running:
        
        # 1. Create protobuf message
        # message = ProtobufConverter.create_message(
        #     message_type="request",
        #     payload={"method": "list_tools", "params": {}}
        # )
        
        # 2. Convert tool to protobuf
        # tool_proto = ProtobufConverter.tool_to_proto(tool_info)
        
        # 3. Handle streaming responses
        # async for response in stream_handler.stream_tool_results(...):
        #     process_response(response)
        
        print("Protocol buffer utilities are available for:")
        print("- Message serialization/deserialization")
        print("- Tool schema conversion")
        print("- Streaming response handling")
        print("- gRPC service integration")
        
        # For now, show the regular client functionality
        health = await client.health_check()
        print(f"Health status: {health['status']}")


async def grpc_server_example():
    """Example of starting gRPC server"""
    print("=== gRPC Server Example ===")
    
    # This would start a gRPC server if protobuf files were generated:
    
    # config = Config()
    # async with CodexClient(config) as client:
    #     server = CodexGRPCServer(client, host="localhost", port=50051)
    #     await server.start()
    #     print("gRPC server started on localhost:50051")
    #     await server.wait_for_termination()
    
    print("To enable gRPC server:")
    print("1. Run: python generate_proto.py")
    print("2. Install: pip install grpcio grpcio-tools")
    print("3. Start the server with the code above")


if __name__ == "__main__":
    print("Note: This example requires generated protobuf files.")
    print("Run 'python generate_proto.py' first to generate them.")
    print()
    
    asyncio.run(protobuf_example())
    print()
    asyncio.run(grpc_server_example())