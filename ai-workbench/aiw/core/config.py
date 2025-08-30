"""
Configuration management for AI Development Workbench
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from .models import Config, UIConfig, BackendConfig, Repository


class ConfigManager:
    """Manages application configuration with file persistence"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            # Default to user's home directory
            self.config_dir = Path.home() / ".ai-workbench"
        else:
            self.config_dir = Path(config_dir)

        self.config_file = self.config_dir / "config.json"
        self._config: Optional[Config] = None

    @property
    def config(self) -> Config:
        """Get the current configuration, loading if necessary"""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self) -> Config:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Config(**data)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Warning: Failed to load config file: {e}")
                return self._create_default_config()
        else:
            return self._create_default_config()

    def save_config(self) -> None:
        """Save current configuration to file"""
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Convert config to dict and save
        config_dict = self.config.model_dump()
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, default=str)

    def _create_default_config(self) -> Config:
        """Create default configuration"""
        return Config()

    def update_ui_config(self, **kwargs) -> None:
        """Update UI configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config.ui, key):
                setattr(self.config.ui, key, value)
        self.save_config()

    def update_backend_config(self, **kwargs) -> None:
        """Update backend configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config.backend, key):
                setattr(self.config.backend, key, value)
        self.save_config()

    def add_repository(self, repo: Repository) -> None:
        """Add a repository to the list"""
        # Remove if already exists
        self.config.repositories = [
            r for r in self.config.repositories
            if r.path != repo.path
        ]
        self.config.repositories.append(repo)
        self.save_config()

    def remove_repository(self, repo_path: str) -> None:
        """Remove a repository from the list"""
        self.config.repositories = [
            r for r in self.config.repositories
            if r.path != repo_path
        ]
        self.save_config()

    def get_recent_repositories(self, limit: int = 10) -> list[Repository]:
        """Get recently opened repositories"""
        # Sort by last_opened, most recent first
        sorted_repos = sorted(
            self.config.repositories,
            key=lambda r: r.last_opened or datetime.min,
            reverse=True
        )
        return sorted_repos[:limit]

    def update_repository_last_opened(self, repo_path: str) -> None:
        """Update the last opened time for a repository"""
        from datetime import datetime
        for repo in self.config.repositories:
            if repo.path == repo_path:
                repo.last_opened = datetime.now()
                break
        self.save_config()

    def get_codex_path(self) -> Optional[str]:
        """Get the configured Codex executable path"""
        if self.config.backend.codex_path:
            return self.config.backend.codex_path

        # Try to find it in the default location relative to ai-workbench
        default_path = Path(__file__).parent.parent.parent.parent / "codex-main" / "codex-rs" / "target" / "debug" / "codex.exe"
        if default_path.exists():
            return str(default_path)

        return None

    def set_codex_path(self, path: str) -> None:
        """Set the Codex executable path"""
        self.update_backend_config(codex_path=path)

    def get_window_geometry(self) -> Optional[Dict[str, Any]]:
        """Get saved window geometry"""
        return self.config.window_geometry

    def set_window_geometry(self, geometry: Dict[str, Any]) -> None:
        """Save window geometry"""
        self.config.window_geometry = geometry
        self.save_config()

    def add_recent_workflow(self, workflow_id: str) -> None:
        """Add a workflow to recent list"""
        if workflow_id in self.config.recent_workflows:
            self.config.recent_workflows.remove(workflow_id)
        self.config.recent_workflows.insert(0, workflow_id)
        # Keep only last 10
        self.config.recent_workflows = self.config.recent_workflows[:10]
        self.save_config()

    def get_recent_workflows(self) -> list[str]:
        """Get recent workflows"""
        return self.config.recent_workflows.copy()


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> Config:
    """Get the current configuration"""
    return get_config_manager().config
