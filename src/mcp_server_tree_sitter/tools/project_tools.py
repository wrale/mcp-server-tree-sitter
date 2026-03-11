"""Project, configuration, language, and cache management tool handlers."""

import logging
import os
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from ..config import ConfigDict
from ..di import get_container
from ..exceptions import ProjectError

logger = logging.getLogger(__name__)


def register_project_tools(mcp_server: FastMCP) -> None:
    """Register project, config, language, and cache tools."""

    @mcp_server.tool()
    def configure(
        config_path: Optional[str] = None,
        cache_enabled: Optional[bool] = None,
        max_file_size_mb: Optional[int] = None,
        log_level: Optional[str] = None,
    ) -> ConfigDict:
        """Configure the server.

        Args:
            config_path: Path to YAML config file
            cache_enabled: Whether to enable parse tree caching
            max_file_size_mb: Maximum file size in MB
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

        Returns:
            Current configuration
        """
        container = get_container()
        config_manager = container.config_manager
        tree_cache = container.tree_cache

        initial_config = config_manager.get_config()
        logger.info(
            f"Initial configuration: "
            f"cache.max_size_mb = {initial_config.cache.max_size_mb}, "
            f"security.max_file_size_mb = {initial_config.security.max_file_size_mb}, "
            f"language.default_max_depth = {initial_config.language.default_max_depth}"
        )

        if config_path:
            logger.info(f"Configuring server with YAML config from: {config_path}")
            abs_path = os.path.abspath(config_path)
            logger.info(f"Absolute path: {abs_path}")

            if not os.path.exists(abs_path):
                logger.error(f"Config file does not exist: {abs_path}")

            config_manager.load_from_file(abs_path)

        if cache_enabled is not None:
            logger.info(f"Setting cache.enabled to {cache_enabled}")
            config_manager.update_value("cache.enabled", cache_enabled)
            tree_cache.set_enabled(cache_enabled)

        if max_file_size_mb is not None:
            logger.info(f"Setting security.max_file_size_mb to {max_file_size_mb}")
            config_manager.update_value("security.max_file_size_mb", max_file_size_mb)

        if log_level is not None:
            logger.info(f"Setting log_level to {log_level}")
            config_manager.update_value("log_level", log_level)

        return config_manager.to_dict()

    @mcp_server.tool()
    def register_project_tool(
        path: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a project directory for code exploration.

        Args:
            path: Path to the project directory
            name: Optional name for the project (defaults to directory name)
            description: Optional description of the project

        Returns:
            Project information
        """
        container = get_container()
        project_registry = container.project_registry
        language_registry = container.language_registry
        try:
            project = project_registry.register_project(name or path, path, description)
            project.scan_files(language_registry)
            return project.to_dict()
        except Exception as e:
            raise ProjectError(f"Failed to register project: {e}") from e

    @mcp_server.tool()
    def list_projects_tool() -> List[Dict[str, Any]]:
        """List all registered projects.

        Returns:
            List of project information
        """
        return get_container().project_registry.list_projects()

    @mcp_server.tool()
    def remove_project_tool(name: str) -> Dict[str, str]:
        """Remove a registered project.

        Args:
            name: Project name

        Returns:
            Success message
        """
        try:
            get_container().project_registry.remove_project(name)
            return {"status": "success", "message": f"Project '{name}' removed"}
        except Exception as e:
            raise ProjectError(f"Failed to remove project: {e}") from e

    @mcp_server.tool()
    def list_languages() -> Dict[str, Any]:
        """List available languages.

        Returns:
            Information about available languages
        """
        available = get_container().language_registry.list_available_languages()
        return {
            "available": available,
            "installable": [],
        }

    @mcp_server.tool()
    def check_language_available(language: str) -> Dict[str, str]:
        """Check if a tree-sitter language parser is available.

        Args:
            language: Language to check

        Returns:
            Success message
        """
        language_registry = get_container().language_registry
        if language_registry.is_language_available(language):
            return {
                "status": "success",
                "message": f"Language '{language}' is available via tree-sitter-language-pack",
            }
        return {
            "status": "error",
            "message": f"Language '{language}' is not available",
        }

    @mcp_server.tool()
    def clear_cache(project: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, str]:
        """Clear the parse tree cache.

        Args:
            project: Optional project to clear cache for
            file_path: Optional specific file to clear cache for

        Returns:
            Status message
        """
        container = get_container()
        project_registry = container.project_registry
        tree_cache = container.tree_cache
        if project and file_path:
            project_obj = project_registry.get_project(project)
            abs_path = project_obj.get_file_path(file_path)
            tree_cache.invalidate(abs_path)
            message = f"Cache cleared for {file_path} in project {project}"
        elif project:
            tree_cache.invalidate()
            message = f"Cache cleared for project {project}"
        else:
            tree_cache.invalidate()
            message = "All caches cleared"

        return {"status": "success", "message": message}

    @mcp_server.tool()
    def diagnose_config(config_path: str) -> Dict[str, Any]:
        """Diagnose issues with YAML configuration loading.

        Args:
            config_path: Path to YAML config file

        Returns:
            Diagnostic information
        """
        from .debug import diagnose_yaml_config

        return diagnose_yaml_config(config_path)
