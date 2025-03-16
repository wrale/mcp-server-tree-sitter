"""Persistent MCP server implementation for Tree-sitter."""

import logging
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from .tools.project import list_projects, register_project, remove_project

logger = logging.getLogger(__name__)

# Create a new MCP instance
mcp = FastMCP("Tree-Sitter Code Explorer")


# Define project-related tools that directly use the stable tool functions
@mcp.tool()
def register_project_tool(
    path: str, name: str = None, description: str = None
) -> Dict[str, Any]:
    """Register a project directory for code exploration.

    Args:
        path: Path to the project directory
        name: Optional name for the project (defaults to directory name)
        description: Optional description of the project

    Returns:
        Project information
    """
    result = register_project(path, name, description)
    logger.debug(f"Registered project: {result.get('name')}")
    return result


@mcp.tool()
def list_projects_tool() -> List[Dict[str, Any]]:
    """List all registered projects.

    Returns:
        List of project information
    """
    result = list_projects()
    logger.debug(f"Listed {len(result)} projects")
    return result


@mcp.tool()
def remove_project_tool(name: str) -> Dict[str, str]:
    """Remove a registered project.

    Args:
        name: Project name

    Returns:
        Success message
    """
    result = remove_project(name)
    logger.debug(f"Removed project: {name}")
    return result


# Use importlib to copy all other tools from the base server
# This would be added in a production version, but is omitted here for simplicity
