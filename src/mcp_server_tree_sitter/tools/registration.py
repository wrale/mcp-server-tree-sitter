"""Tool and prompt registration for MCP server.

Wires up handlers: project_tools, file_tools, ast_tools, search_tools, analysis_tools.
Tools get shared state at call time via get_app().
"""

from mcp.server.fastmcp import FastMCP

from ..app import get_app
from .analysis_tools import register_analysis_tools
from .ast_tools import register_ast_tools
from .file_tools import register_file_tools
from .project_tools import register_project_tools
from .search_tools import register_search_tools


def register_tools(mcp_server: FastMCP) -> None:
    """Register all MCP tools. Tools get shared state via get_app() at call time.

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
    """Register all prompt templates. Prompts use get_app() at call time."""

    @mcp_server.prompt()
    def code_review(project: str, file_path: str) -> str:
        """Create a prompt for reviewing a code file"""
        from .analysis import extract_symbols
        from .file_operations import get_file_content

        app = get_app()
        project_obj = app.project_registry.get_project(project)
        content = get_file_content(project_obj, file_path)
        language = app.language_registry.language_for_file(file_path)

        structure = ""
        try:
            symbols = extract_symbols(project_obj, file_path, app.language_registry)

            if symbols.get("functions"):
                structure += "\nFunctions:\n"
                for func in symbols["functions"]:
                    structure += f"- {func['name']}\n"

            if symbols.get("classes"):
                structure += "\nClasses:\n"
                for cls in symbols["classes"]:
                    structure += f"- {cls['name']}\n"
        except Exception:
            pass

        text = content.decode(errors="replace") if isinstance(content, bytes) else content
        return f"""
        Please review this {language} code file:

        ```{language}
        {text}
        ```

        {structure}

        Focus on:
        1. Code clarity and organization
        2. Potential bugs or issues
        3. Performance considerations
        4. Best practices for {language}
        """

    @mcp_server.prompt()
    def explain_code(project: str, file_path: str, focus: str | None = None) -> str:
        """Create a prompt for explaining a code file"""
        from .file_operations import get_file_content

        app = get_app()
        project_obj = app.project_registry.get_project(project)
        content = get_file_content(project_obj, file_path)
        language = app.language_registry.language_for_file(file_path)

        focus_prompt = ""
        if focus:
            focus_prompt = f"\nPlease focus specifically on explaining: {focus}"

        text = content.decode(errors="replace") if isinstance(content, bytes) else content
        return f"""
        Please explain this {language} code file:

        ```{language}
        {text}
        ```

        Provide a clear explanation of:
        1. What this code does
        2. How it's structured
        3. Any important patterns or techniques used
        {focus_prompt}
        """

    @mcp_server.prompt()
    def explain_tree_sitter_query() -> str:
        """Create a prompt explaining tree-sitter query syntax"""
        return """
        Tree-sitter queries use S-expression syntax to match patterns in code.

        Basic query syntax:
        - `(node_type)` - Match nodes of a specific type
        - `(node_type field: (child_type))` - Match nodes with specific field relationships
        - `@name` - Capture a node with a name
        - `#predicate` - Apply additional constraints

        Example query for Python functions:
        ```
        (function_definition
          name: (identifier) @function.name
          parameters: (parameters) @function.params
          body: (block) @function.body) @function.def
        ```

        Please write a tree-sitter query to find:
        """

    @mcp_server.prompt()
    def suggest_improvements(project: str, file_path: str) -> str:
        """Create a prompt for suggesting code improvements"""
        from .analysis import analyze_code_complexity
        from .file_operations import get_file_content

        app = get_app()
        project_obj = app.project_registry.get_project(project)
        content = get_file_content(project_obj, file_path)
        language = app.language_registry.language_for_file(file_path)

        try:
            complexity = analyze_code_complexity(project_obj, file_path, app.language_registry)
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
        except Exception:
            complexity_info = ""

        text = content.decode(errors="replace") if isinstance(content, bytes) else content
        return f"""
        Please suggest improvements for this {language} code:

        ```{language}
        {text}
        ```

        {complexity_info}

        Suggest specific, actionable improvements for:
        1. Code quality and readability
        2. Performance optimization
        3. Error handling and robustness
        4. Following {language} best practices

        Where possible, provide code examples of your suggestions.
        """

    @mcp_server.prompt()
    def project_overview(project: str) -> str:
        """Create a prompt for a project overview analysis"""
        from .analysis import analyze_project_structure

        app = get_app()
        project_obj = app.project_registry.get_project(project)

        try:
            analysis = analyze_project_structure(project_obj, app.language_registry)

            languages_str = "\n".join(f"- {lang}: {count} files" for lang, count in analysis["languages"].items())

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

        except Exception:
            languages_str = "Error analyzing languages"
            entry_points_str = "Error detecting entry points"
            build_files_str = "Error detecting build files"

        return f"""
        Please analyze this codebase:

        Project name: {project_obj.name}
        Path: {project_obj.root_path}

        Languages:
        {languages_str}

        Possible entry points:
        {entry_points_str}

        Build configuration:
        {build_files_str}

        Based on this information, please:
        1. Provide an overview of what this project seems to be
        2. Identify the main components and their relationships
        3. Suggest where to start exploring the codebase
        4. Identify any patterns or architectural approaches used
        """
