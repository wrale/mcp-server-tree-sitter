"""API functions for accessing container dependencies.

This module provides function-based access to dependencies managed by the
container, helping to break circular import chains and simplify access.
"""

import logging
from typing import Any, Dict, List, Optional

from .di import get_container
from .exceptions import ProjectError

logger = logging.getLogger(__name__)


def get_project_registry() -> Any:
    """Get the project registry."""
    return get_container().project_registry


def get_language_registry() -> Any:
    """Get the language registry."""
    return get_container().language_registry


def get_tree_cache() -> Any:
    """Get the tree cache."""
    return get_container().tree_cache


def get_config() -> Any:
    """Get the current configuration."""
    return get_container().get_config()


def get_config_manager() -> Any:
    """Get the configuration manager."""
    return get_container().config_manager


def register_project(path: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """Register a project."""
    project_registry = get_project_registry()
    language_registry = get_language_registry()

    try:
        # Register project
        project = project_registry.register_project(name or path, path, description)

        # Scan for languages
        project.scan_files(language_registry)

        project_dict = project.to_dict()
        # Add type annotations
        result: Dict[str, Any] = {
            "name": project_dict["name"],
            "root_path": project_dict["root_path"],
            "description": project_dict["description"],
            "languages": project_dict["languages"],
            "last_scan_time": project_dict["last_scan_time"],
        }
        return result
    except Exception as e:
        raise ProjectError(f"Failed to register project: {e}") from e


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


def clear_cache(project: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, str]:
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
