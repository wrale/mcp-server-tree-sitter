"""Tool and prompt registration for MCP server.

Wires up handlers: project_tools, file_tools, ast_tools, search_tools, analysis_tools.
Tools get shared state at call time via api getters (get_project_registry, get_config, etc.).
"""

from mcp.server.fastmcp import FastMCP

from .analysis_tools import register_analysis_tools
from .ast_tools import register_ast_tools
from .file_tools import register_file_tools
from .project_tools import register_project_tools
from .search_tools import register_search_tools


def register_tools(mcp_server: FastMCP) -> None:
    """Register all MCP tools. Tools get shared state via api getters at call time.

    Args:
        mcp_server: MCP server instance
    """
    register_project_tools(mcp_server)
    register_file_tools(mcp_server)
    register_ast_tools(mcp_server)
    register_search_tools(mcp_server)
    register_analysis_tools(mcp_server)
    _register_prompts(mcp_server)


def _register_prompts(mcp_server: FastMCP) -> None:
    """Register all prompt templates. Prompt bodies from .prompt_handlers."""
    from .prompt_handlers import (
        code_review_prompt_body,
        explain_code_prompt_body,
        explain_tree_sitter_query_prompt_body,
        project_overview_prompt_body,
        suggest_improvements_prompt_body,
    )

    @mcp_server.prompt()
    def code_review(project: str, file_path: str) -> str:
        """Create a prompt for reviewing a code file"""
        return code_review_prompt_body(project, file_path)

    @mcp_server.prompt()
    def explain_code(project: str, file_path: str, focus: str | None = None) -> str:
        """Create a prompt for explaining a code file"""
        return explain_code_prompt_body(project, file_path, focus)

    @mcp_server.prompt()
    def explain_tree_sitter_query() -> str:
        """Create a prompt explaining tree-sitter query syntax"""
        return explain_tree_sitter_query_prompt_body()

    @mcp_server.prompt()
    def suggest_improvements(project: str, file_path: str) -> str:
        """Create a prompt for suggesting code improvements"""
        return suggest_improvements_prompt_body(project, file_path)

    @mcp_server.prompt()
    def project_overview(project: str) -> str:
        """Create a prompt for a project overview analysis"""
        return project_overview_prompt_body(project)
