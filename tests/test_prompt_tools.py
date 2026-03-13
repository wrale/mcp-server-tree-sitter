"""Functional tests for the 5 prompt tools.

Prompts: code_review, explain_code, explain_tree_sitter_query,
suggest_improvements, project_overview.
Covers: output validation, error handling when analysis fails, unsupported language.
"""

import contextlib
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.test_helpers import (
    code_review_prompt,
    explain_code_prompt,
    explain_tree_sitter_query_prompt,
    project_overview_prompt,
    register_project_tool,
    remove_project_tool,
    suggest_improvements_prompt,
)

PROJECT_NAME = "prompt_tools_test_project"


@pytest.fixture
def project_with_python_file(tmp_path: Path) -> Generator[tuple[str, Path], None, None]:
    """Register a temp project with a small Python file."""
    (tmp_path / "main.py").write_text(
        "def greet(name: str) -> str:\n    return f'Hello, {name}'\n\nclass Helper:\n    pass\n"
    )
    register_project_tool(path=str(tmp_path), name=PROJECT_NAME)
    try:
        yield PROJECT_NAME, tmp_path
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(PROJECT_NAME)


@pytest.fixture
def project_with_unknown_extension(tmp_path: Path) -> Generator[tuple[str, Path], None, None]:
    """Register a temp project with a file that has no known language (unsupported)."""
    (tmp_path / "script.xyz").write_text("some content\nline2\n")
    register_project_tool(path=str(tmp_path), name=PROJECT_NAME)
    try:
        yield PROJECT_NAME, tmp_path
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(PROJECT_NAME)


# ---- explain_tree_sitter_query (no project/file, static) ----


def test_explain_tree_sitter_query_output_validation() -> None:
    """explain_tree_sitter_query returns non-empty prompt with expected structure."""
    result = explain_tree_sitter_query_prompt()
    assert isinstance(result, str)
    assert len(result.strip()) > 0
    assert "tree-sitter" in result.lower() or "query" in result.lower()
    assert "syntax" in result.lower() or "match" in result.lower() or "node" in result.lower()
    assert "Please write" in result or "write" in result.lower()


# ---- code_review ----


def test_code_review_output_validation(project_with_python_file: tuple[str, Path]) -> None:
    """code_review returns prompt containing language, code block, and structure or fallback."""
    name, root = project_with_python_file
    result = code_review_prompt(project=name, file_path="main.py")
    assert isinstance(result, str)
    assert len(result.strip()) > 0
    assert "python" in result.lower()
    assert "main.py" not in result or "greet" in result or "Helper" in result
    assert "def greet" in result or "Hello" in result
    assert "Functions:" in result or "Classes:" in result or "review" in result.lower()
    assert "Focus on:" in result or "clarity" in result.lower() or "best practices" in result.lower()


def test_code_review_error_handling_when_symbol_extraction_fails(
    project_with_python_file: tuple[str, Path],
) -> None:
    """When extract_symbols fails, code_review still returns valid prompt with fallback message."""
    name, _ = project_with_python_file
    with patch(
        "mcp_server_tree_sitter.tools.prompt_handlers.extract_symbols",
        side_effect=RuntimeError("symbol extraction failed"),
    ):
        result = code_review_prompt(project=name, file_path="main.py")
    assert isinstance(result, str)
    assert "Structure could not be extracted" in result or "reviewing code only" in result
    assert "python" in result.lower()
    assert "def greet" in result or "Hello" in result


def test_code_review_unsupported_language(project_with_unknown_extension: tuple[str, Path]) -> None:
    """Unsupported language (unknown extension) yields prompt with 'unknown' language."""
    name, _ = project_with_unknown_extension
    result = code_review_prompt(project=name, file_path="script.xyz")
    assert isinstance(result, str)
    assert "unknown" in result.lower()
    assert "some content" in result or "line2" in result


# ---- explain_code ----


def test_explain_code_output_validation(project_with_python_file: tuple[str, Path]) -> None:
    """explain_code returns prompt with language, code block, and explanation instructions."""
    name, _ = project_with_python_file
    result = explain_code_prompt(project=name, file_path="main.py")
    assert isinstance(result, str)
    assert "python" in result.lower()
    assert "def greet" in result or "Hello" in result
    assert "explain" in result.lower()
    assert "focus" in result.lower() or "What this code does" in result


def test_explain_code_with_focus(project_with_python_file: tuple[str, Path]) -> None:
    """explain_code with focus includes the focus text in the prompt."""
    name, _ = project_with_python_file
    result = explain_code_prompt(
        project=name, file_path="main.py", focus="the Helper class"
    )
    assert "the Helper class" in result
    assert "focus" in result.lower()


def test_explain_code_unsupported_language(
    project_with_unknown_extension: tuple[str, Path],
) -> None:
    """Unsupported language yields prompt with 'unknown'."""
    name, _ = project_with_unknown_extension
    result = explain_code_prompt(project=name, file_path="script.xyz")
    assert "unknown" in result.lower()
    assert "some content" in result or "line2" in result


# ---- suggest_improvements ----


def test_suggest_improvements_output_validation(
    project_with_python_file: tuple[str, Path],
) -> None:
    """suggest_improvements returns prompt with language, code, and metrics or fallback."""
    name, _ = project_with_python_file
    result = suggest_improvements_prompt(project=name, file_path="main.py")
    assert isinstance(result, str)
    assert "python" in result.lower()
    assert "def greet" in result or "Hello" in result
    assert "Line count" in result or "Code metrics" in result or "metrics" in result.lower()
    assert "improvements" in result.lower() or "Suggest" in result


def test_suggest_improvements_error_handling_when_complexity_fails(
    project_with_python_file: tuple[str, Path],
) -> None:
    """When analyze_code_complexity fails, suggest_improvements still returns valid prompt with fallback."""
    name, _ = project_with_python_file
    with patch(
        "mcp_server_tree_sitter.tools.prompt_handlers.analyze_code_complexity",
        side_effect=ValueError("complexity failed"),
    ):
        result = suggest_improvements_prompt(project=name, file_path="main.py")
    assert isinstance(result, str)
    assert "Code metrics could not be computed" in result or "could not be computed" in result
    assert "python" in result.lower()
    assert "def greet" in result or "Hello" in result


def test_suggest_improvements_unsupported_language(
    project_with_unknown_extension: tuple[str, Path],
) -> None:
    """Unsupported language yields prompt with 'unknown'."""
    name, _ = project_with_unknown_extension
    result = suggest_improvements_prompt(project=name, file_path="script.xyz")
    assert "unknown" in result.lower()
    assert "some content" in result or "line2" in result


# ---- project_overview ----


def test_project_overview_output_validation(
    project_with_python_file: tuple[str, Path],
) -> None:
    """project_overview returns prompt with project name, path, and language/file info."""
    name, root = project_with_python_file
    result = project_overview_prompt(project=name)
    assert isinstance(result, str)
    assert PROJECT_NAME in result or name in result
    assert str(root) in result
    assert "python" in result.lower() or "Languages:" in result or "files" in result.lower()
    assert "entry points" in result.lower() or "Entry" in result
    assert "overview" in result.lower() or "analyze" in result.lower()


def test_project_overview_error_handling_when_structure_analysis_fails(
    project_with_python_file: tuple[str, Path],
) -> None:
    """When analyze_project_structure fails, project_overview returns prompt with error placeholders."""
    name, root = project_with_python_file
    with patch(
        "mcp_server_tree_sitter.tools.prompt_handlers.analyze_project_structure",
        side_effect=RuntimeError("structure analysis failed"),
    ):
        result = project_overview_prompt(project=name)
    assert isinstance(result, str)
    assert "Error analyzing languages" in result or "Error detecting" in result
    assert PROJECT_NAME in result or name in result
    assert str(root) in result
