"""Edge-case tests for register_project_tool."""

import contextlib
from pathlib import Path

import pytest

from mcp_server_tree_sitter.exceptions import ProjectError
from tests.test_helpers import register_project_tool, remove_project_tool


def test_register_project_tool_nonexistent_path() -> None:
    """Non-existent directory path raises ProjectError."""
    with pytest.raises(ProjectError) as exc_info:
        register_project_tool(path="/nonexistent/dir/xyz_123", name="nonexistent_test")
    assert "exist" in str(exc_info.value).lower() or "path" in str(exc_info.value).lower()


def test_register_project_tool_path_is_file_not_directory(tmp_path: Path) -> None:
    """Path that is a file (not a directory) raises ProjectError."""
    a_file = tmp_path / "a_file.txt"
    a_file.write_text("hello")
    with pytest.raises(ProjectError) as exc_info:
        register_project_tool(path=str(a_file), name="file_as_project")
    assert "directory" in str(exc_info.value).lower() or "not" in str(exc_info.value).lower()


def test_register_project_tool_same_path_twice_same_name(tmp_path: Path) -> None:
    """Registering the same path twice with the same name raises on second attempt."""
    name = "same_path_twice_project"
    register_project_tool(path=str(tmp_path), name=name)
    try:
        with pytest.raises(ProjectError) as exc_info:
            register_project_tool(path=str(tmp_path), name=name)
        assert "already exists" in str(exc_info.value) or name in str(exc_info.value)
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(name)


def test_register_project_tool_symlink_to_directory(tmp_path: Path) -> None:
    """Symlink to a directory: registration succeeds (resolves to real path)."""
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    (real_dir / "f.py").write_text("x = 1\n")
    link_dir = tmp_path / "link_to_real"
    try:
        link_dir.symlink_to(real_dir)
    except OSError:
        pytest.skip("Symlinks not supported on this system")
    name = "symlink_project"
    try:
        result = register_project_tool(path=str(link_dir), name=name)
        assert result.get("name") == name
        assert "file_count" in result or "languages" in result
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(name)


def test_register_project_tool_path_insufficient_read_permissions(
    tmp_path: Path,
) -> None:
    """Path with insufficient read permissions raises ProjectError (or OSError wrapped)."""
    no_read = tmp_path / "no_read_dir"
    no_read.mkdir()
    (no_read / "f.py").write_text("x = 1\n")
    try:
        no_read.chmod(0o000)
    except OSError:
        pytest.skip("Cannot chmod 000 on this system")
    name = "no_read_project"
    try:
        with pytest.raises(ProjectError):
            register_project_tool(path=str(no_read), name=name)
    finally:
        no_read.chmod(0o755)
