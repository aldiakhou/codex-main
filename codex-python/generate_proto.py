# Build script for generating Python protobuf files
import os
import subprocess
import sys
from pathlib import Path

def generate_protobuf_files():
    """Generate Python protobuf files from .proto files"""
    
    proto_dir = Path("proto")
    output_dir = Path("src/codex_python/proto")
    
    if not proto_dir.exists():
        print("Error: proto directory not found")
        return False
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all .proto files
    proto_files = list(proto_dir.glob("*.proto"))
    
    if not proto_files:
        print("No .proto files found")
        return False
    
    # Generate protobuf files
    for proto_file in proto_files:
        cmd = [
            "python", "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(proto_file)
        ]
        
        print(f"Generating {proto_file.name}...")
        try:
            subprocess.run(cmd, check=True)
            print(f"Successfully generated {proto_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating {proto_file.name}: {e}")
            return False
    
    # Create __init__.py files
    init_files = [
        output_dir / "__init__.py",
        output_dir / "proto" / "__init__.py"
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")
    
    return True

if __name__ == "__main__":
    success = generate_protobuf_files()
    sys.exit(0 if success else 1)