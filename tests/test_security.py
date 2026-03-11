"""Tests for security module (path traversal, symlinks, extensions, file size)."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_server_tree_sitter.exceptions import SecurityError
from mcp_server_tree_sitter.utils.security import validate_file_access


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """A temporary project root."""
    return tmp_path.resolve()


def test_path_traversal_outside_root(project_root: Path) -> None:
    """Path traversal (e.g. ../../etc/passwd) is rejected."""
    # Resolve to a path outside project_root
    outside = project_root / ".." / ".." / "etc" / "passwd"
    resolved = outside.resolve()
    if str(resolved).startswith(str(project_root)):
        pytest.skip("Path resolves inside project on this system")
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = []
        m.return_value.security.allowed_extensions = None
        m.return_value.security.max_file_size_mb = 10
        with pytest.raises(SecurityError) as exc_info:
            validate_file_access(resolved, project_root)
        assert "outside project root" in str(exc_info.value)


def test_path_traversal_relative_inside_root(project_root: Path) -> None:
    """A path that stays inside project root is allowed (no traversal)."""
    (project_root / "sub").mkdir(exist_ok=True)
    inside = project_root / "sub" / "file.py"
    inside.write_text("x")
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = []
        m.return_value.security.allowed_extensions = None
        m.return_value.security.max_file_size_mb = 10
        validate_file_access(inside, project_root)  # no raise


def test_symlink_bypass_rejected(project_root: Path) -> None:
    """Symlink pointing outside project root is rejected (resolve follows symlink)."""
    (project_root / "link_target").mkdir(exist_ok=True)
    link_path = project_root / "mylink"
    try:
        link_path.symlink_to(os.path.abspath(os.path.join(project_root, "..")))
    except OSError:
        pytest.skip("Cannot create symlink (e.g. Windows without privilege)")
    # Resolved path is parent of project_root, so outside
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = []
        m.return_value.security.allowed_extensions = None
        m.return_value.security.max_file_size_mb = 10
        with pytest.raises(SecurityError) as exc_info:
            validate_file_access(link_path, project_root)
        assert "outside project root" in str(exc_info.value)


def test_file_with_no_extension_when_extensions_allowed(project_root: Path) -> None:
    """When allowed_extensions is set, file with no extension is rejected."""
    no_ext = project_root / "Makefile"  # or any path with no suffix
    no_ext.write_text("all:\n")
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = []
        m.return_value.security.allowed_extensions = ["py", "js", "ts"]
        m.return_value.security.max_file_size_mb = 10
        with pytest.raises(SecurityError) as exc_info:
            validate_file_access(project_root / "noext", project_root)
        assert "not allowed" in str(exc_info.value) or "File type" in str(exc_info.value)


def test_allowed_extension_filtering(project_root: Path) -> None:
    """Allowed extensions are enforced; disallowed extension raises."""
    py_file = project_root / "a.py"
    py_file.write_text("x")
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = []
        m.return_value.security.allowed_extensions = ["py"]
        m.return_value.security.max_file_size_mb = 10
        validate_file_access(py_file, project_root)  # allowed

    js_file = project_root / "b.js"
    js_file.write_text("x")
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = []
        m.return_value.security.allowed_extensions = ["py"]
        m.return_value.security.max_file_size_mb = 10
        with pytest.raises(SecurityError) as exc_info:
            validate_file_access(js_file, project_root)
        assert "not allowed" in str(exc_info.value) or "File type" in str(exc_info.value)


def test_allowed_extensions_none_permits_any(project_root: Path) -> None:
    """When allowed_extensions is None, any extension is allowed."""
    f = project_root / "any.xyz"
    f.write_text("x")
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = []
        m.return_value.security.allowed_extensions = None
        m.return_value.security.max_file_size_mb = 10
        validate_file_access(f, project_root)  # no raise


def test_file_size_limit_enforcement(project_root: Path) -> None:
    """File larger than max_file_size_mb raises SecurityError."""
    big = project_root / "big.py"
    # > 1 MB
    with open(big, "w") as fp:
        fp.write("# " + "x" * 998 + "\n")
        for _ in range(1100):
            fp.write("# " + "x" * 998 + "\n")
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = []
        m.return_value.security.allowed_extensions = None
        m.return_value.security.max_file_size_mb = 1
        with pytest.raises(SecurityError) as exc_info:
            validate_file_access(big, project_root)
        assert "too large" in str(exc_info.value).lower() or "exceeds" in str(exc_info.value).lower()


def test_excluded_directory_rejected(project_root: Path) -> None:
    """Path under an excluded directory raises SecurityError."""
    (project_root / ".git").mkdir(exist_ok=True)
    (project_root / ".git" / "config").write_text("x")
    with patch("mcp_server_tree_sitter.utils.security.get_config") as m:
        m.return_value.security.excluded_dirs = [".git"]
        m.return_value.security.allowed_extensions = None
        m.return_value.security.max_file_size_mb = 10
        with pytest.raises(SecurityError) as exc_info:
            validate_file_access(project_root / ".git" / "config", project_root)
        assert "excluded" in str(exc_info.value).lower() or "Access denied" in str(exc_info.value)
