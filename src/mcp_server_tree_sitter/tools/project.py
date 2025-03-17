"""Project management tools for MCP server."""

from typing import Any, Dict, List, Optional

from ..api import get_language_registry, get_project_registry
from ..exceptions import ProjectError


def register_project(path: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a project for code analysis.

    Args:
        path: Path to the project directory
        name: Optional name for the project (defaults to directory name)
        description: Optional description

    Returns:
        Project information
    """
    # Get dependencies from API
    project_registry = get_project_registry()
    language_registry = get_language_registry()

    try:
        # Register project
        project = project_registry.register_project(name or path, path, description)

        # Scan for languages
        project.scan_files(language_registry)

        project_dict = project.to_dict()
        # Add type annotations for clarity
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


def get_project(name: str) -> Dict[str, Any]:
    """
    Get project information.

    Args:
        name: Project name

    Returns:
        Project information
    """
    # Get dependency from API
    project_registry = get_project_registry()

    try:
        project = project_registry.get_project(name)
        project_dict = project.to_dict()
        # Add type annotations for clarity
        result: Dict[str, Any] = {
            "name": project_dict["name"],
            "root_path": project_dict["root_path"],
            "description": project_dict["description"],
            "languages": project_dict["languages"],
            "last_scan_time": project_dict["last_scan_time"],
        }
        return result
    except Exception as e:
        raise ProjectError(f"Failed to get project: {e}") from e


def list_projects() -> List[Dict[str, Any]]:
    """
    List all registered projects.

    Returns:
        List of project information
    """
    # Get dependency from API
    project_registry = get_project_registry()

    projects_list = project_registry.list_projects()
    # Explicitly create a typed list
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
    """
    Remove a project.

    Args:
        name: Project name

    Returns:
        Success message
    """
    # Get dependency from API
    project_registry = get_project_registry()

    try:
        project_registry.remove_project(name)
        return {"status": "success", "message": f"Project '{name}' removed"}
    except Exception as e:
        raise ProjectError(f"Failed to remove project: {e}") from e
