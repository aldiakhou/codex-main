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
    
    # Ensure package marker in output dir only
    pkg_init = output_dir / "__init__.py"
    if not pkg_init.exists():
        pkg_init.touch()
        print(f"Created {pkg_init}")
    
    return True

if __name__ == "__main__":
    success = generate_protobuf_files()
    sys.exit(0 if success else 1)
