"""Tool and prompt registration for MCP server.

Wires up handlers: project_tools, file_tools, ast_tools, search_tools, analysis_tools.
Tools get shared state at call time via api getters (get_project_registry, get_config, etc.).
"""

from mcp.server.fastmcp import FastMCP

from ..api import get_language_registry, get_project_registry
from ..bootstrap import get_logger
from .analysis_tools import register_analysis_tools
from .ast_tools import register_ast_tools
from .file_tools import register_file_tools
from .project_tools import register_project_tools
from .search_tools import register_search_tools

logger = get_logger(__name__)


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
    """Register all prompt templates. Prompts use api getters at call time; bodies live in prompts.mcp_prompts."""
    from ..prompts.mcp_prompts import (
        build_code_review_prompt,
        build_explain_code_prompt,
        build_explain_tree_sitter_query_prompt,
        build_project_overview_prompt,
        build_suggest_improvements_prompt,
    )

    @mcp_server.prompt()
    def code_review(project: str, file_path: str) -> str:
        """Create a prompt for reviewing a code file"""
        from .analysis import extract_symbols
        from .file_operations import get_file_content

        project_obj = get_project_registry().get_project(project)
        content = get_file_content(project_obj, file_path)
        language = get_language_registry().language_for_file(file_path) or "unknown"

        structure = ""
        try:
            symbols = extract_symbols(project_obj, file_path, get_language_registry())
            if symbols.get("functions"):
                structure += "\nFunctions:\n"
                for func in symbols["functions"]:
                    structure += f"- {func['name']}\n"
            if symbols.get("classes"):
                structure += "\nClasses:\n"
                for cls in symbols["classes"]:
                    structure += f"- {cls['name']}\n"
        except Exception as e:
            logger.warning("Symbol extraction failed for code_review prompt: %s", e)
            structure = "\n(Structure could not be extracted; reviewing code only.)"

        text = content.decode(errors="replace") if isinstance(content, bytes) else content
        return build_code_review_prompt(text, language, structure)

    @mcp_server.prompt()
    def explain_code(project: str, file_path: str, focus: str | None = None) -> str:
        """Create a prompt for explaining a code file"""
        from .file_operations import get_file_content

        project_obj = get_project_registry().get_project(project)
        content = get_file_content(project_obj, file_path)
        language = get_language_registry().language_for_file(file_path) or "unknown"
        text = content.decode(errors="replace") if isinstance(content, bytes) else content
        return build_explain_code_prompt(text, language, focus)

    @mcp_server.prompt()
    def explain_tree_sitter_query() -> str:
        """Create a prompt explaining tree-sitter query syntax"""
        return build_explain_tree_sitter_query_prompt()

    @mcp_server.prompt()
    def suggest_improvements(project: str, file_path: str) -> str:
        """Create a prompt for suggesting code improvements"""
        from .analysis import analyze_code_complexity
        from .file_operations import get_file_content

        project_obj = get_project_registry().get_project(project)
        content = get_file_content(project_obj, file_path)
        language = get_language_registry().language_for_file(file_path) or "unknown"

        complexity_info = ""
        try:
            complexity = analyze_code_complexity(project_obj, file_path, get_language_registry())
            complexity_info = f"""
            Code metrics:
            - Line count: {complexity["line_count"]}
            - Code lines: {complexity["code_lines"]}
            - Comment lines: {complexity["comment_lines"]}
            - Comment ratio: {complexity["comment_ratio"]:.1%}
            - Functions: {complexity["function_count"]}
            - Classes: {complexity["class_count"]}
            - Avg. function length: {complexity["avg_function_lines"]} lines
            - Cyclomatic complexity: {complexity["cyclomatic_complexity"]}
            """
        except Exception as e:
            logger.warning("Complexity analysis failed for suggest_improvements prompt: %s", e)
            complexity_info = "\n(Code metrics could not be computed.)"

        text = content.decode(errors="replace") if isinstance(content, bytes) else content
        return build_suggest_improvements_prompt(text, language, complexity_info)

    @mcp_server.prompt()
    def project_overview(project: str) -> str:
        """Create a prompt for a project overview analysis"""
        from .analysis import analyze_project_structure

        project_obj = get_project_registry().get_project(project)

        try:
            analysis = analyze_project_structure(project_obj, get_language_registry())
            languages_str = "\n".join(
                f"- {lang}: {count} files" for lang, count in analysis["languages"].items()
            )
            entry_points_str = (
                "\n".join(f"- {entry['path']} ({entry['language']})" for entry in analysis["entry_points"])
                if analysis["entry_points"]
                else "None detected"
            )
            build_files_str = (
                "\n".join(f"- {file['path']} ({file['type']})" for file in analysis["build_files"])
                if analysis["build_files"]
                else "None detected"
            )
        except Exception as e:
            logger.warning("Project structure analysis failed for project_overview prompt: %s", e)
            languages_str = "Error analyzing languages"
            entry_points_str = "Error detecting entry points"
            build_files_str = "Error detecting build files"

        return build_project_overview_prompt(
            project_obj.name,
            str(project_obj.root_path),
            languages_str,
            entry_points_str,
            build_files_str,
        )
