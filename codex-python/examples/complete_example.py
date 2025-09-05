"""
Complete example of Codex Python usage with all components
"""

import asyncio
import json
from pathlib import Path

from codex_python.core.orchestrator import CodexOrchestrator, CodexOperation
from codex_python.core.config import Config


async def main():
    """Complete example of Codex Python usage"""
    
    print("🚀 Codex Python - Complete Example")
    print("=" * 50)
    
    # Create configuration
    config = Config()
    
    # Add example servers
    config.servers["filesystem"] = config.ServerConfig(
        name="filesystem",
        command="echo",
        args=["Example filesystem server"],
        transport="stdio"
    )
    
    # Create orchestrator
    orchestrator = CodexOrchestrator(config)
    await orchestrator.initialize()
    
    # Create session
    session_id = "demo_session"
    working_dir = str(Path.cwd())
    session = orchestrator.create_session(session_id, working_dir, user="demo_user")
    
    try:
        print(f"✅ Created session: {session_id}")
        
        # 1. Chat with LLM
        print("\n💬 Testing LLM Chat...")
        try:
            async for response in orchestrator.chat(
                ["Hello! I'm Codex. How can I help you with your coding tasks today?"],
                session_id=session_id,
                stream=True
            ):
                print(f"LLM: {response}")
        except Exception as e:
            print(f"⚠️  LLM chat failed (expected if no LLM configured): {e}")
        
        # 2. Execute safe command
        print("\n⚡ Testing Command Execution...")
        result = await orchestrator.execute_command(
            ["echo", "Hello from Codex!"],
            session_id=session_id,
            require_approval=False  # Skip approval for demo
        )
        
        if result.success:
            print(f"✅ Command executed successfully")
            print(f"   Output: {result.result['stdout'].strip()}")
        else:
            print(f"❌ Command failed: {result.error}")
        
        # 3. Search files
        print("\n🔍 Testing File Search...")
        result = await orchestrator.search_files(
            "*.py",
            session_id=session_id,
            max_results=5
        )
        
        if result.success:
            print(f"✅ Found {len(result.result)} Python files")
            for search_result in result.result[:3]:  # Show first 3
                print(f"   - {search_result.path}")
        else:
            print(f"❌ Search failed: {result.error}")
        
        # 4. Create and apply a simple patch
        print("\n🔧 Testing Patch Application...")
        
        # Create a simple test file
        test_file = Path(working_dir) / "test_file.txt"
        test_file.write_text("Original content\n")
        
        # Create a patch
        patch_content = """--- test_file.txt
+++ test_file.txt
@@ -1 +1 @@
-Original content
+Modified content
+Added line
"""
        
        result = await orchestrator.apply_patch(
            patch_content,
            session_id=session_id,
            require_approval=False  # Skip approval for demo
        )
        
        if result.success:
            print("✅ Patch applied successfully")
            print(f"   Modified content: {test_file.read_text().strip()}")
        else:
            print(f"❌ Patch failed: {result.error}")
        
        # 5. Test policy evaluation
        print("\n🛡️  Testing Policy Evaluation...")
        
        # Test safe command
        safe_result = await orchestrator.execute_command(
            ["ls", "-la"],
            session_id=session_id,
            require_approval=False
        )
        
        if safe_result.success:
            print("✅ Safe command allowed by policy")
        else:
            print(f"❌ Safe command blocked: {safe_result.error}")
        
        # Test dangerous command (will be blocked)
        dangerous_result = await orchestrator.execute_command(
            ["rm", "-rf", "/tmp/something"],
            session_id=session_id,
            require_approval=False
        )
        
        if not dangerous_result.success:
            print("✅ Dangerous command properly blocked by policy")
        else:
            print("⚠️  Dangerous command was allowed (unexpected)")
        
        # 6. Test approval workflow
        print("\n👥 Testing Approval Workflow...")
        
        # Create a context that requires approval
        approval_context = {
            "operation": "test_operation",
            "description": "Test approval workflow",
            "requester": "demo_user",
            "risk_score": 0.7
        }
        
        print("Approval workflow would be triggered for high-risk operations")
        print("In a real implementation, this would prompt for user approval")
        
        # 7. Get status
        print("\n📊 Getting System Status...")
        status = await orchestrator.get_status(session_id)
        
        print("System Status:")
        print(f"  - Orchestrator: {'✅ Initialized' if status['orchestrator']['initialized'] else '❌ Not initialized'}")
        print(f"  - Active Sessions: {status['orchestrator']['active_sessions']}")
        print(f"  - MCP Health: {status['mcp']['status']}")
        print(f"  - Pending Approvals: {status['approval']['pending_requests']}")
        
        # 8. Show operation history
        print(f"\n📈 Operation History ({len(orchestrator.operation_history)} operations):")
        for op in orchestrator.operation_history[-3:]:  # Show last 3
            status_icon = "✅" if op.success else "❌"
            print(f"  {status_icon} {op.operation.value} ({op.execution_time:.2f}s)")
        
        # 9. Test sandboxing
        print("\n🔒 Testing Sandboxing...")
        
        sandbox_result = await orchestrator.execute_command(
            ["python", "-c", "print('Sandbox test')"],
            session_id=session_id,
            require_approval=False
        )
        
        if sandbox_result.success:
            sandboxed = sandbox_result.metadata.get("sandboxed", False)
            print(f"✅ Command executed {'in sandbox' if sandboxed else 'normally'}")
            print(f"   Output: {sandbox_result.result['stdout'].strip()}")
        
        # 10. Cleanup
        print("\n🧹 Cleaning up...")
        
        # Remove test file
        if test_file.exists():
            test_file.unlink()
            print("✅ Test file removed")
        
        # Close session
        orchestrator.close_session(session_id)
        print("✅ Session closed")
        
        # Final status
        final_status = await orchestrator.get_status()
        print(f"\n🎯 Final Status: {final_status['orchestrator']['active_sessions']} active sessions")
        
    except Exception as e:
        print(f"❌ Error during example: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up orchestrator
        await orchestrator.cleanup()
        print("\n✅ Orchestrator cleaned up")


async def advanced_example():
    """Advanced example showing more complex workflows"""
    
    print("\n🎯 Advanced Example - Multi-step Workflow")
    print("=" * 50)
    
    # Configuration with more options
    config = Config()
    config.enable_sandbox = True
    config.log_level = "DEBUG"
    
    orchestrator = CodexOrchestrator(config)
    await orchestrator.initialize()
    
    session_id = "advanced_session"
    working_dir = str(Path.cwd())
    orchestrator.create_session(session_id, working_dir, user="advanced_user")
    
    try:
        # 1. Complex workflow: Search -> Analyze -> Patch
        print("🔍 Step 1: Search for Python files...")
        search_result = await orchestrator.search_files(
            "*.py",
            session_id=session_id,
            max_results=10,
            search_content=True
        )
        
        if search_result.success and search_result.result:
            print(f"Found {len(search_result.result)} Python files")
            
            # 2. Analyze found files
            print("\n📊 Step 2: Analyze files...")
            for result in search_result.result[:3]:
                print(f"  - {result.path} ({result.size} bytes)")
                
                # Could use LLM to analyze file content here
                # analysis = await orchestrator.chat([
                #     f"Analyze this file: {result.path}"
                # ], session_id=session_id)
        
        # 3. Demonstrate error handling
        print("\n⚠️  Step 3: Error handling demonstration...")
        
        # Try to execute a command that should fail
        bad_command = await orchestrator.execute_command(
            ["this_command_does_not_exist"],
            session_id=session_id,
            require_approval=False
        )
        
        if not bad_command.success:
            print(f"✅ Properly handled error: {bad_command.error}")
        
        # 4. Show comprehensive status
        print("\n📈 Step 4: Comprehensive status...")
        status = await orchestrator.get_status(session_id)
        
        print("Comprehensive Status:")
        for category, data in status.items():
            if isinstance(data, dict):
                print(f"  {category}:")
                for key, value in data.items():
                    print(f"    {key}: {value}")
            else:
                print(f"  {category}: {data}")
        
    except Exception as e:
        print(f"❌ Advanced example error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        orchestrator.close_session(session_id)
        await orchestrator.cleanup()


if __name__ == "__main__":
    print("🎭 Codex Python - Complete Implementation Demo")
    print("This demonstrates all major components of the Codex Python system")
    print()
    
    # Run basic example
    asyncio.run(main())
    
    # Run advanced example
    asyncio.run(advanced_example())
    
    print("\n🎉 Demo completed!")
    print("\nKey components demonstrated:")
    print("✅ LLM Client with multiple provider support")
    print("✅ MCP (Model Context Protocol) integration")
    print("✅ Command execution with policy enforcement")
    print("✅ Approval workflow system")
    print("✅ Sandboxing with platform-specific security")
    print("✅ High-performance file search")
    print("✅ Patch application system")
    print("✅ Session management")
    print("✅ Comprehensive error handling")
    print("✅ Status monitoring and metrics")
    
    print("\n🔧 To extend this implementation:")
    print("1. Add real LLM provider API keys")
    print("2. Configure actual MCP servers")
    print("3. Customize security policies")
    print("4. Add domain-specific tools")
    print("5. Integrate with your existing workflow")