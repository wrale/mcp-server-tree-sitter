"""Project, configuration, language, and cache management tool handlers."""

import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..api import get_config_manager, get_language_registry, get_project_registry, get_tree_cache
from ..cache.parser_cache import TreeCache
from ..config import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_FILE_SIZE_MB,
    VALID_LOG_LEVELS,
    ConfigDict,
    ConfigurationManager,
)
from ..exceptions import ProjectError

logger = logging.getLogger(__name__)


def apply_configure(
    config_manager: ConfigurationManager,
    tree_cache: TreeCache,
    *,
    config_path: str | None = None,
    cache_enabled: bool | None = None,
    max_file_size_mb: int | None = None,
    log_level: str | None = None,
) -> ConfigDict:
    """Apply configure options to config_manager and tree_cache. Single place for validation and keep-previous logic."""
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
        if max_file_size_mb >= 1:
            logger.info(f"Setting security.max_file_size_mb to {max_file_size_mb}")
            config_manager.update_value("security.max_file_size_mb", max_file_size_mb)
        else:
            current = config_manager.get_config().security.max_file_size_mb
            if current >= 1:
                logger.warning(
                    "max_file_size_mb=%s invalid (must be >= 1), keeping current value %s",
                    max_file_size_mb,
                    current,
                )
            else:
                logger.warning(
                    "max_file_size_mb=%s invalid (must be >= 1), using default %s",
                    max_file_size_mb,
                    DEFAULT_MAX_FILE_SIZE_MB,
                )
                config_manager.update_value(
                    "security.max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB
                )

    if log_level is not None:
        if log_level in VALID_LOG_LEVELS:
            logger.info(f"Setting log_level to {log_level}")
            config_manager.update_value("log_level", log_level)
        else:
            current = config_manager.get_config().log_level
            if current in VALID_LOG_LEVELS:
                logger.warning(
                    "log_level=%r invalid (must be one of %s), keeping current value %r",
                    log_level,
                    VALID_LOG_LEVELS,
                    current,
                )
            else:
                logger.warning(
                    "log_level=%r invalid (must be one of %s), using default %r",
                    log_level,
                    VALID_LOG_LEVELS,
                    DEFAULT_LOG_LEVEL,
                )
                config_manager.update_value("log_level", DEFAULT_LOG_LEVEL)

    return config_manager.to_dict()


def register_project_tools(mcp_server: FastMCP) -> None:
    """Register project, config, language, and cache tools."""

    @mcp_server.tool()
    def configure(
        config_path: str | None = None,
        cache_enabled: bool | None = None,
        max_file_size_mb: int | None = None,
        log_level: str | None = None,
    ) -> ConfigDict:
        """Set server options. Only provided args are applied; others keep current value.

        Args:
            config_path: Path to YAML config file. Defaults to None (no change).
            cache_enabled: Enable/disable parse tree cache. Defaults to None (no change).
            max_file_size_mb: Max file size in MB. Defaults to None (no change).
            log_level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to None (no change).

        Returns:
            Dict with cache, security, language, log_level (current config after apply).

        Note:
            Invalid config_path is logged; file load errors may leave config unchanged.
        """
        return apply_configure(
            get_config_manager(),
            get_tree_cache(),
            config_path=config_path,
            cache_enabled=cache_enabled,
            max_file_size_mb=max_file_size_mb,
            log_level=log_level,
        )

    @mcp_server.tool()
    def register_project_tool(
        path: str, name: str | None = None, description: str | None = None
    ) -> dict[str, Any]:
        """Register a project root for code exploration.

        Args:
            path: Path to the project directory.
            name: Project name. Defaults to path (directory name).
            description: Optional project description. Defaults to None.

        Returns:
            Dict with name, path, description, file_count (and related keys).

        Raises:
            ProjectError: If path is invalid or registration fails.
        """
        project_registry = get_project_registry()
        language_registry = get_language_registry()
        try:
            project = project_registry.register_project(name or path, path, description)
            project.scan_files(language_registry)
            return project.to_dict()
        except Exception as e:
            raise ProjectError(f"Failed to register project: {e}") from e

    @mcp_server.tool()
    def list_projects_tool() -> list[dict[str, Any]]:
        """List all registered projects.

        Returns:
            List of dicts with name, path, description, file_count (and related keys).
            Empty list if no projects registered.
        """
        return get_project_registry().list_projects()

    @mcp_server.tool()
    def remove_project_tool(name: str) -> dict[str, str]:
        """Remove a registered project by name.

        Args:
            name: Project name to remove.

        Returns:
            Dict with status ('success') and message.

        Raises:
            ProjectError: If project not found or removal fails.
        """
        try:
            get_project_registry().remove_project(name)
            return {"status": "success", "message": f"Project '{name}' removed"}
        except Exception as e:
            raise ProjectError(f"Failed to remove project: {e}") from e

    @mcp_server.tool()
    def list_languages() -> dict[str, Any]:
        """List tree-sitter languages available for parsing.

        Returns:
            Dict with 'available' (list of language ids) and 'installable' (list).
        """
        available = get_language_registry().list_available_languages()
        return {
            "available": available,
            "installable": [],
        }

    @mcp_server.tool()
    def check_language_available(language: str) -> dict[str, str]:
        """Check if a tree-sitter parser exists for the given language.

        Args:
            language: Language identifier to check (e.g. 'python', 'javascript').

        Returns:
            Dict with status ('success' or 'error') and message.
            Unavailable languages return status 'error', not an exception.
        """
        language_registry = get_language_registry()
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
    def clear_cache(project: str | None = None, file_path: str | None = None) -> dict[str, str]:
        """Clear parse tree cache.

        Args:
            project: Project name to clear. Defaults to None (clear all projects).
            file_path: Path within project to clear. Defaults to None.
                If project is set and file_path is set, only that file is cleared.
                If project is set and file_path is None, entire project cache cleared.

        Returns:
            Dict with status ('success') and message.

        Raises:
            ProjectError: If project is unknown when project or file_path is provided.
        """
        project_registry = get_project_registry()
        tree_cache = get_tree_cache()
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
    def diagnose_config(config_path: str) -> dict[str, Any]:
        """Run diagnostics on a YAML config file.

        Args:
            config_path: Path to the YAML config file.

        Returns:
            Dict with load result, errors (if any), and effective config values.
            Missing or invalid file is reported in the diagnostic, not via exception.
        """
        from .debug import diagnose_yaml_config

        return diagnose_yaml_config(config_path)
