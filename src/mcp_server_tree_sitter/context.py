"""Context class for managing dependency injection.

This module provides a ServerContext class to manage dependencies
and provide a cleaner interface for interacting with the application's
components while supporting dependency injection.
"""

from typing import Any, Dict, List, Optional

# Import logging from bootstrap package
from .bootstrap import get_logger, update_log_levels
from .cache.parser_cache import TreeCache
from .config import ConfigurationManager, ServerConfig
from .di import get_container
from .exceptions import ProjectError
from .language.registry import LanguageRegistry
from .models.project import ProjectRegistry

logger = get_logger(__name__)


class ServerContext:
    """Context for managing application state with dependency injection."""

    def __init__(
        self,
        config_manager: Optional[ConfigurationManager] = None,
        project_registry: Optional[ProjectRegistry] = None,
        language_registry: Optional[LanguageRegistry] = None,
        tree_cache: Optional[TreeCache] = None,
    ):
        """
        Initialize with optional components.

        If components are not provided, they will be fetched from the global container.
        """
        container = get_container()
        self.config_manager = config_manager or container.config_manager
        self.project_registry = project_registry or container.project_registry
        self.language_registry = language_registry or container.language_registry
        self.tree_cache = tree_cache or container.tree_cache

    def get_config(self) -> ServerConfig:
        """Get the current configuration."""
        return self.config_manager.get_config()

    # Project management methods
    def register_project(
        self, path: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a project for code analysis."""
        try:
            # Register project
            project = self.project_registry.register_project(name or path, path, description)

            # Scan for languages
            project.scan_files(self.language_registry)

            return project.to_dict()
        except Exception as e:
            raise ProjectError(f"Failed to register project: {e}") from e

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all registered projects."""
        return self.project_registry.list_projects()

    def remove_project(self, name: str) -> Dict[str, str]:
        """Remove a registered project."""
        self.project_registry.remove_project(name)
        return {"status": "success", "message": f"Project '{name}' removed"}

    # Cache management methods
    def clear_cache(self, project: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, str]:
        """Clear the parse tree cache."""
        if project and file_path:
            # Get file path
            project_obj = self.project_registry.get_project(project)
            abs_path = project_obj.get_file_path(file_path)

            # Clear cache
            self.tree_cache.invalidate(abs_path)
            return {"status": "success", "message": f"Cache cleared for {file_path} in {project}"}
        else:
            # Clear all
            self.tree_cache.invalidate()
            return {"status": "success", "message": "Cache cleared"}

    # Configuration management methods
    def configure(
        self,
        config_path: Optional[str] = None,
        cache_enabled: Optional[bool] = None,
        max_file_size_mb: Optional[int] = None,
        log_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Configure the server."""
        # Load config if path provided
        if config_path:
            logger.info(f"Configuring server with YAML config from: {config_path}")
            self.config_manager.load_from_file(config_path)

        # Update specific settings
        if cache_enabled is not None:
            logger.info(f"Setting cache.enabled to {cache_enabled}")
            self.config_manager.update_value("cache.enabled", cache_enabled)
            self.tree_cache.set_enabled(cache_enabled)

        if max_file_size_mb is not None:
            logger.info(f"Setting security.max_file_size_mb to {max_file_size_mb}")
            self.config_manager.update_value("security.max_file_size_mb", max_file_size_mb)

        if log_level is not None:
            logger.info(f"Setting log_level to {log_level}")
            self.config_manager.update_value("log_level", log_level)

            # Apply log level using centralized bootstrap function
            update_log_levels(log_level)
            logger.info(f"Applied log level {log_level} to mcp_server_tree_sitter loggers")

        # Return current config as dict
        return self.config_manager.to_dict()


# Create a global context instance for convenience
global_context = ServerContext()


def get_global_context() -> ServerContext:
    """Get the global server context."""
    return global_context
