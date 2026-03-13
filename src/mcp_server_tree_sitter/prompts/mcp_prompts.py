"""MCP prompt template bodies.

Prompt text and structure live here; tools/registration.py fetches data
and calls these builders to keep prompts discoverable and editable in one place.
"""


def build_code_review_prompt(content: str, language: str, structure: str) -> str:
    """Build the code_review prompt body from file content, language, and symbol structure."""
    return f"""
        Please review this {language} code file:

        ```{language}
        {content}
        ```

        {structure}

        Focus on:
        1. Code clarity and organization
        2. Potential bugs or issues
        3. Performance considerations
        4. Best practices for {language}
        """


def build_explain_code_prompt(content: str, language: str, focus: str | None = None) -> str:
    """Build the explain_code prompt body."""
    focus_prompt = ""
    if focus:
        focus_prompt = f"\nPlease focus specifically on explaining: {focus}"
    return f"""
        Please explain this {language} code file:

        ```{language}
        {content}
        ```

        Provide a clear explanation of:
        1. What this code does
        2. How it's structured
        3. Any important patterns or techniques used
        {focus_prompt}
        """


def build_explain_tree_sitter_query_prompt() -> str:
    """Build the explain_tree_sitter_query prompt body (static template)."""
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


def build_suggest_improvements_prompt(
    content: str, language: str, complexity_info: str
) -> str:
    """Build the suggest_improvements prompt body."""
    return f"""
        Please suggest improvements for this {language} code:

        ```{language}
        {content}
        ```

        {complexity_info}

        Suggest specific, actionable improvements for:
        1. Code quality and readability
        2. Performance optimization
        3. Error handling and robustness
        4. Following {language} best practices

        Where possible, provide code examples of your suggestions.
        """


def build_project_overview_prompt(
    project_name: str,
    project_path: str,
    languages_str: str,
    entry_points_str: str,
    build_files_str: str,
) -> str:
    """Build the project_overview prompt body."""
    return f"""
        Please analyze this codebase:

        Project name: {project_name}
        Path: {project_path}

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
