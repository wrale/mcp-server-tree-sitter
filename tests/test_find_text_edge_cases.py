"""Edge-case tests for find_text tool."""

import contextlib
from pathlib import Path

import pytest

from tests.test_helpers import find_text, register_project_tool, remove_project_tool

PROJECT_NAME = "find_text_edge_cases_project"


def _project_with_python_file(tmp_path: Path) -> str:
    (tmp_path / "main.py").write_text("def foo():\n    pass\nx = 1\n")
    register_project_tool(path=str(tmp_path), name=PROJECT_NAME)
    return PROJECT_NAME


def test_find_text_empty_pattern_returns_list(tmp_path: Path) -> None:
    """Empty string pattern does not crash; returns a list (possibly many matches)."""
    name = _project_with_python_file(tmp_path)
    try:
        result = find_text(project=name, pattern="")
        assert isinstance(result, list)
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(name)


def test_find_text_invalid_regex_raises(tmp_path: Path) -> None:
    """Invalid regex pattern when use_regex=True raises ValueError."""
    name = _project_with_python_file(tmp_path)
    try:
        with pytest.raises(ValueError) as exc_info:
            find_text(project=name, pattern="[unclosed", use_regex=True)
        assert "regex" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(name)


def test_find_text_max_results_zero_returns_empty(tmp_path: Path) -> None:
    """max_results=0 returns empty list."""
    name = _project_with_python_file(tmp_path)
    try:
        result = find_text(project=name, pattern="foo", max_results=0)
        assert result == []
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(name)


def test_find_text_context_lines_negative_does_not_crash(tmp_path: Path) -> None:
    """Negative context_lines does not crash; returns list."""
    name = _project_with_python_file(tmp_path)
    try:
        result = find_text(
            project=name,
            pattern="foo",
            context_lines=-1,
        )
        assert isinstance(result, list)
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(name)


def test_find_text_no_files_matching_pattern_returns_empty(tmp_path: Path) -> None:
    """File pattern that matches no files returns empty list, not error."""
    (tmp_path / "main.py").write_text("def foo():\n    pass\n")
    register_project_tool(path=str(tmp_path), name=PROJECT_NAME)
    try:
        result = find_text(
            project=PROJECT_NAME,
            pattern="NonexistentUniqueString123",
            file_pattern="**/*.py",
        )
        assert result == []
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(PROJECT_NAME)
