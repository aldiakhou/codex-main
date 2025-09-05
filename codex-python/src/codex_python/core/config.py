"""
Core configuration management for Codex Python
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from pathlib import Path


@dataclass
class ServerConfig:
    """Configuration for MCP server connection"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"  # stdio, sse, streamable_http
    url: Optional[str] = None
    timeout: float = 30.0


@dataclass
class AuthConfig:
    """Authentication configuration"""
    type: str  # oauth, bearer, none
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token_url: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    bearer_token: Optional[str] = None


@dataclass
class Config:
    """Main configuration class for Codex Python"""
    
    # Server configurations
    servers: Dict[str, ServerConfig] = field(default_factory=dict)
    
    # Authentication
    auth: AuthConfig = field(default_factory=lambda: AuthConfig(type="none"))
    
    # Global settings
    timeout: float = 30.0
    log_level: str = "INFO"
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Transport settings
    default_transport: str = "stdio"
    enable_websocket: bool = True
    websocket_url: Optional[str] = None
    
    # Tool management
    tool_timeout: float = 60.0
    max_concurrent_tools: int = 10
    
    # Security
    allowed_tools: List[str] = field(default_factory=list)
    blocked_tools: List[str] = field(default_factory=list)
    enable_sandbox: bool = True

    # Approval and history
    approval_policy: str = "on_request"  # on_request, on_failure, unless_trusted, never
    history_enabled: bool = True
    history_path: Optional[str] = None
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "Config":
        """Load configuration from file (JSON or TOML)."""
        import json
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        suffix = config_path.suffix.lower()
        if suffix in (".toml", ".tml"):
            return cls.from_toml(config_path)
        # default JSON
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_toml(cls, path: Union[str, Path]) -> "Config":
        """Load configuration from TOML file; lenient mapping to current fields."""
        p = Path(path)
        try:
            import tomllib as _toml
        except Exception:
            import toml as _toml  # type: ignore
        data = _toml.loads(p.read_text(encoding="utf-8"))
        # Map likely structure: [servers.<name>] entries with command/args/env/transport/url/timeout
        servers_dict = {}
        servers = data.get("servers", {})
        if isinstance(servers, dict):
            for name, s in servers.items():
                if not isinstance(s, dict):
                    continue
                servers_dict[name] = ServerConfig(
                    name=name,
                    command=s.get("command", ""),
                    args=s.get("args", []) or [],
                    env=s.get("env", {}) or {},
                    transport=s.get("transport", "stdio"),
                    url=s.get("url"),
                    timeout=float(s.get("timeout", 30.0)),
                )
        auth = data.get("auth", {}) or {}
        auth_cfg = AuthConfig(
            type=str(auth.get("type", "none")),
            client_id=auth.get("client_id"),
            client_secret=auth.get("client_secret"),
            token_url=auth.get("token_url"),
            scopes=auth.get("scopes", []) or [],
            bearer_token=auth.get("bearer_token"),
        )
        return cls(
            servers=servers_dict,
            auth=auth_cfg,
            timeout=float(data.get("timeout", 30.0)),
            log_level=str(data.get("log_level", "INFO")),
            max_retries=int(data.get("max_retries", 3)),
            retry_delay=float(data.get("retry_delay", 1.0)),
            default_transport=str(data.get("default_transport", "stdio")),
            enable_websocket=bool(data.get("enable_websocket", True)),
            websocket_url=data.get("websocket_url"),
            tool_timeout=float(data.get("tool_timeout", 60.0)),
            max_concurrent_tools=int(data.get("max_concurrent_tools", 10)),
            allowed_tools=data.get("allowed_tools", []) or [],
            blocked_tools=data.get("blocked_tools", []) or [],
            enable_sandbox=bool(data.get("enable_sandbox", True)),
        )
    
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create configuration from dictionary"""
        servers = {}
        for name, server_data in data.get("servers", {}).items():
            servers[name] = ServerConfig(
                name=name,
                **server_data
            )
        
        auth_data = data.get("auth", {})
        auth = AuthConfig(
            type=auth_data.get("type", "none"),
            client_id=auth_data.get("client_id"),
            client_secret=auth_data.get("client_secret"),
            token_url=auth_data.get("token_url"),
            scopes=auth_data.get("scopes", []),
            bearer_token=auth_data.get("bearer_token")
        )
        
        return cls(
            servers=servers,
            auth=auth,
            timeout=data.get("timeout", 30.0),
            log_level=data.get("log_level", "INFO"),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 1.0),
            default_transport=data.get("default_transport", "stdio"),
            enable_websocket=data.get("enable_websocket", True),
            websocket_url=data.get("websocket_url"),
            tool_timeout=data.get("tool_timeout", 60.0),
            max_concurrent_tools=data.get("max_concurrent_tools", 10),
            allowed_tools=data.get("allowed_tools", []),
            blocked_tools=data.get("blocked_tools", []),
            enable_sandbox=data.get("enable_sandbox", True),
            approval_policy=data.get("approval_policy", "on_request"),
            history_enabled=bool(data.get("history_enabled", True)),
            history_path=data.get("history_path")
        )
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        servers = {}
        
        # Parse server configurations from environment
        server_count = int(os.getenv("CODEX_SERVER_COUNT", "0"))
        for i in range(server_count):
            prefix = f"CODEX_SERVER_{i}_"
            name = os.getenv(f"{prefix}NAME", f"server_{i}")
            
            args = []
            arg_count = int(os.getenv(f"{prefix}ARG_COUNT", "0"))
            for j in range(arg_count):
                arg = os.getenv(f"{prefix}ARG_{j}", "")
                if arg:
                    args.append(arg)
            
            servers[name] = ServerConfig(
                name=name,
                command=os.getenv(f"{prefix}COMMAND", ""),
                args=args,
                transport=os.getenv(f"{prefix}TRANSPORT", "stdio"),
                url=os.getenv(f"{prefix}URL"),
                timeout=float(os.getenv(f"{prefix}TIMEOUT", "30.0"))
            )
        
        # Authentication from environment
        auth_type = os.getenv("CODEX_AUTH_TYPE", "none")
        auth = AuthConfig(type=auth_type)
        
        if auth_type == "oauth":
            auth.client_id = os.getenv("CODEX_CLIENT_ID")
            auth.client_secret = os.getenv("CODEX_CLIENT_SECRET")
            auth.token_url = os.getenv("CODEX_TOKEN_URL")
            auth.scopes = os.getenv("CODEX_SCOPES", "").split(",")
        elif auth_type == "bearer":
            auth.bearer_token = os.getenv("CODEX_BEARER_TOKEN")
        
        return cls(
            servers=servers,
            auth=auth,
            timeout=float(os.getenv("CODEX_TIMEOUT", "30.0")),
            log_level=os.getenv("CODEX_LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("CODEX_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("CODEX_RETRY_DELAY", "1.0")),
            default_transport=os.getenv("CODEX_DEFAULT_TRANSPORT", "stdio"),
            enable_websocket=os.getenv("CODEX_ENABLE_WEBSOCKET", "true").lower() == "true",
            websocket_url=os.getenv("CODEX_WEBSOCKET_URL"),
            tool_timeout=float(os.getenv("CODEX_TOOL_TIMEOUT", "60.0")),
            max_concurrent_tools=int(os.getenv("CODEX_MAX_CONCURRENT_TOOLS", "10")),
            allowed_tools=os.getenv("CODEX_ALLOWED_TOOLS", "").split(",") if os.getenv("CODEX_ALLOWED_TOOLS") else [],
            blocked_tools=os.getenv("CODEX_BLOCKED_TOOLS", "").split(",") if os.getenv("CODEX_BLOCKED_TOOLS") else [],
            enable_sandbox=os.getenv("CODEX_ENABLE_SANDBOX", "true").lower() == "true",
            approval_policy=os.getenv("CODEX_APPROVAL_POLICY", "on_request"),
            history_enabled=os.getenv("CODEX_HISTORY_ENABLED", "true").lower() == "true",
            history_path=os.getenv("CODEX_HISTORY_PATH")
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            "servers": {
                name: {
                    "command": server.command,
                    "args": server.args,
                    "env": server.env,
                    "transport": server.transport,
                    "url": server.url,
                    "timeout": server.timeout
                }
                for name, server in self.servers.items()
            },
            "auth": {
                "type": self.auth.type,
                "client_id": self.auth.client_id,
                "client_secret": self.auth.client_secret,
                "token_url": self.auth.token_url,
                "scopes": self.auth.scopes,
                "bearer_token": self.auth.bearer_token
            },
            "timeout": self.timeout,
            "log_level": self.log_level,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "default_transport": self.default_transport,
            "enable_websocket": self.enable_websocket,
            "websocket_url": self.websocket_url,
            "tool_timeout": self.tool_timeout,
            "max_concurrent_tools": self.max_concurrent_tools,
            "allowed_tools": self.allowed_tools,
            "blocked_tools": self.blocked_tools,
            "enable_sandbox": self.enable_sandbox
            ,"approval_policy": self.approval_policy
            ,"history_enabled": self.history_enabled
            ,"history_path": self.history_path
        }
