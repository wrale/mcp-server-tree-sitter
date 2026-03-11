"""Tests for Project.get_file_path path containment (TASK-09).

Covers: valid relative paths, path traversal attempts, and symlink handling
using is_relative_to for correct containment check.
"""

import os
from pathlib import Path

import pytest

from mcp_server_tree_sitter.exceptions import ProjectError
from mcp_server_tree_sitter.models.project import Project


def test_get_file_path_valid_relative_path(tmp_path: Path) -> None:
    """Valid relative path inside project returns resolved path."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print(1)")
    project = Project("p", tmp_path)
    result = project.get_file_path("src/main.py")
    assert result == (tmp_path / "src" / "main.py").resolve()
    assert result.exists()


def test_get_file_path_relative_path_with_dot(tmp_path: Path) -> None:
    """Path with . (current dir) is accepted when inside project."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "f.py").write_text("x")
    project = Project("p", tmp_path)
    result = project.get_file_path("sub/./f.py")
    assert result == (tmp_path / "sub" / "f.py").resolve()


def test_get_file_path_traversal_raises(tmp_path: Path) -> None:
    """Path traversal (../) outside project root raises ProjectError."""
    (tmp_path / "inside").mkdir()
    project = Project("p", tmp_path)
    with pytest.raises(ProjectError, match="outside project root"):
        project.get_file_path("../etc/passwd")
    with pytest.raises(ProjectError, match="outside project root"):
        project.get_file_path("inside/../../../etc/passwd")
    with pytest.raises(ProjectError, match="outside project root"):
        project.get_file_path("..")


def test_get_file_path_prefix_confusion(tmp_path: Path) -> None:
    """Path that only shares a string prefix with root is rejected (is_relative_to vs startswith)."""
    # e.g. root /proj, path /project/file would wrongly pass startswith("/proj")
    project_root = tmp_path / "proj"
    project_root.mkdir()
    other_dir = tmp_path / "project"
    other_dir.mkdir()
    (other_dir / "file.py").write_text("x")
    project = Project("p", project_root)
    # Resolved path is other_dir/file.py which is not under project_root
    with pytest.raises(ProjectError, match="outside project root"):
        project.get_file_path("../project/file.py")


def test_get_file_path_symlink_outside_raises(tmp_path: Path) -> None:
    """Symlink inside project pointing outside is rejected (resolved path outside root)."""
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks not supported on this platform")
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    link_in_project = project_dir / "link_to_outside"
    try:
        link_in_project.symlink_to(outside)
    except OSError as e:
        pytest.skip(f"symlink creation not allowed: {e}")
    project = Project("p", project_dir)
    # Request path "link_to_outside/secret.txt" resolves to outside/secret.txt -> not under project
    with pytest.raises(ProjectError, match="outside project root"):
        project.get_file_path("link_to_outside/secret.txt")


def test_get_file_path_symlink_inside_ok(tmp_path: Path) -> None:
    """Symlink inside project pointing to another path inside project is accepted."""
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks not supported on this platform")
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "real").mkdir()
    (project_dir / "real" / "file.py").write_text("x")
    link = project_dir / "link"
    try:
        link.symlink_to(project_dir / "real")
    except OSError as e:
        pytest.skip(f"symlink creation not allowed: {e}")
    project = Project("p", project_dir)
    result = project.get_file_path("link/file.py")
    assert result.resolve() == (project_dir / "real" / "file.py").resolve()
    assert result.exists()
