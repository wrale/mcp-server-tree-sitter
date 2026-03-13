"""Shared prompt body logic for MCP prompt tools.

Used by registration.py and by tests (via test_helpers). Single source of truth
for code_review, explain_code, suggest_improvements, and project_overview prompt bodies.
"""

from ..api import get_language_registry, get_project_registry
from ..bootstrap import get_logger
from ..prompts.mcp_prompts import (
    build_code_review_prompt,
    build_explain_code_prompt,
    build_explain_tree_sitter_query_prompt,
    build_project_overview_prompt,
    build_suggest_improvements_prompt,
)
from .analysis import (
    analyze_code_complexity,
    analyze_project_structure,
    extract_symbols,
)
from .file_operations import get_file_content

logger = get_logger(__name__)


def _file_content_text(project: str, file_path: str) -> tuple[str, str]:
    """Return (text_content, language) for a project file."""
    project_obj = get_project_registry().get_project(project)
    content = get_file_content(project_obj, file_path)
    language = get_language_registry().language_for_file(file_path) or "unknown"
    text = content.decode(errors="replace") if isinstance(content, bytes) else content
    return text, language


def code_review_prompt_body(project: str, file_path: str) -> str:
    """Build the code_review prompt body."""
    text, language = _file_content_text(project, file_path)
    structure = ""
    try:
        project_obj = get_project_registry().get_project(project)
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
    return build_code_review_prompt(text, language, structure)


def explain_code_prompt_body(
    project: str, file_path: str, focus: str | None = None
) -> str:
    """Build the explain_code prompt body."""
    text, language = _file_content_text(project, file_path)
    return build_explain_code_prompt(text, language, focus)


def explain_tree_sitter_query_prompt_body() -> str:
    """Build the explain_tree_sitter_query prompt body (static)."""
    return build_explain_tree_sitter_query_prompt()


def suggest_improvements_prompt_body(project: str, file_path: str) -> str:
    """Build the suggest_improvements prompt body."""
    text, language = _file_content_text(project, file_path)
    complexity_info = ""
    try:
        project_obj = get_project_registry().get_project(project)
        complexity = analyze_code_complexity(
            project_obj, file_path, get_language_registry()
        )
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
        logger.warning(
            "Complexity analysis failed for suggest_improvements prompt: %s", e
        )
        complexity_info = "\n(Code metrics could not be computed.)"
    return build_suggest_improvements_prompt(text, language, complexity_info)


def project_overview_prompt_body(project: str) -> str:
    """Build the project_overview prompt body."""
    project_obj = get_project_registry().get_project(project)
    try:
        analysis = analyze_project_structure(
            project_obj, get_language_registry()
        )
        languages_str = "\n".join(
            f"- {lang}: {count} files"
            for lang, count in analysis["languages"].items()
        )
        entry_points_str = (
            "\n".join(
                f"- {entry['path']} ({entry['language']})"
                for entry in analysis["entry_points"]
            )
            if analysis["entry_points"]
            else "None detected"
        )
        build_files_str = (
            "\n".join(
                f"- {file['path']} ({file['type']})"
                for file in analysis["build_files"]
            )
            if analysis["build_files"]
            else "None detected"
        )
    except Exception as e:
        logger.warning(
            "Project structure analysis failed for project_overview prompt: %s",
            e,
        )
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
