"""API helpers for shared app state (project registry, config, cache, etc.)."""

import logging
from typing import Any, Dict, List

from .app import get_app
from .cache.parser_cache import TreeCache
from .config import ConfigurationManager, ServerConfig
from .language.registry import LanguageRegistry
from .models.project import ProjectRegistry

logger = logging.getLogger(__name__)


def get_project_registry() -> ProjectRegistry:
    """Get the project registry."""
    return get_app().project_registry


def get_language_registry() -> LanguageRegistry:
    """Get the language registry."""
    return get_app().language_registry


def get_tree_cache() -> TreeCache:
    """Get the tree cache."""
    return get_app().tree_cache


def get_config() -> ServerConfig:
    """Get the current configuration."""
    return get_app().get_config()


def get_config_manager() -> ConfigurationManager:
    """Get the configuration manager."""
    return get_app().config_manager


def list_projects() -> List[Dict[str, Any]]:
    """List all registered projects."""
    projects_list = get_project_registry().list_projects()
    # Convert to explicitly typed list
    result: List[Dict[str, Any]] = []
    for project in projects_list:
        result.append(
            {
                "name": project["name"],
                "root_path": project["root_path"],
                "description": project["description"],
                "languages": project["languages"],
                "last_scan_time": project["last_scan_time"],
            }
        )
    return result


def remove_project(name: str) -> Dict[str, str]:
    """Remove a registered project."""
    get_project_registry().remove_project(name)
    return {"status": "success", "message": f"Project '{name}' removed"}


def clear_cache(project: str | None = None, file_path: str | None = None) -> Dict[str, str]:
    """Clear the parse tree cache."""
    tree_cache = get_tree_cache()

    if project and file_path:
        # Get file path
        project_registry = get_project_registry()
        project_obj = project_registry.get_project(project)
        abs_path = project_obj.get_file_path(file_path)

        # Clear cache
        tree_cache.invalidate(abs_path)
        return {"status": "success", "message": f"Cache cleared for {file_path} in {project}"}
    else:
        # Clear all
        tree_cache.invalidate()
        return {"status": "success", "message": "Cache cleared"}
