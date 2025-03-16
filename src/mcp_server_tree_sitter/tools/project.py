"""Project management tools for MCP server."""

from typing import Any, Dict, List, Optional

from ..exceptions import ProjectError
from ..models.project import ProjectRegistry

# Global project registry
project_registry = ProjectRegistry()


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
    from ..language.registry import LanguageRegistry

    # Create language registry
    language_registry = LanguageRegistry()

    try:
        # Register project
        project = project_registry.register_project(name or path, path, description)

        # Scan for languages
        project.scan_files(language_registry)

        return project.to_dict()
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
    try:
        project = project_registry.get_project(name)
        return project.to_dict()
    except Exception as e:
        raise ProjectError(f"Failed to get project: {e}") from e


def list_projects() -> List[Dict[str, Any]]:
    """
    List all registered projects.

    Returns:
        List of project information
    """
    return project_registry.list_projects()


def remove_project(name: str) -> Dict[str, str]:
    """
    Remove a project.

    Args:
        name: Project name

    Returns:
        Success message
    """
    try:
        project_registry.remove_project(name)
        return {"status": "success", "message": f"Project '{name}' removed"}
    except Exception as e:
        raise ProjectError(f"Failed to remove project: {e}") from e
