"""Tests for file_operations.py module."""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from mcp_server_tree_sitter.exceptions import FileAccessError
from mcp_server_tree_sitter.tools.file_operations import (
    count_lines,
    get_file_content,
    get_file_info,
    list_project_files,
)
from tests.test_helpers import register_project_tool


@pytest.fixture
def test_project() -> Generator[Dict[str, Any], None, None]:
    """Create a temporary test project with various file types."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create different file types
        # Python file
        python_file = project_path / "test.py"
        with open(python_file, "w") as f:
            f.write("def hello():\n    print('Hello, world!')\n\nhello()\n")

        # Text file
        text_file = project_path / "readme.txt"
        with open(text_file, "w") as f:
            f.write("This is a readme file.\nIt has multiple lines.\n")

        # Empty file
        empty_file = project_path / "empty.md"
        empty_file.touch()

        # Nested directory structure
        nested_dir = project_path / "nested"
        nested_dir.mkdir()
        nested_file = nested_dir / "nested.py"
        with open(nested_file, "w") as f:
            f.write("# A nested Python file\n")

        # A large file
        large_file = project_path / "large.log"
        with open(large_file, "w") as f:
            f.write("Line " + "x" * 100 + "\n" * 1000)  # 1000 lines with 100+ chars each

        # A hidden file and directory
        hidden_dir = project_path / ".hidden"
        hidden_dir.mkdir()
        hidden_file = hidden_dir / "hidden.txt"
        with open(hidden_file, "w") as f:
            f.write("This is a hidden file.\n")

        # Register the project
        project_name = "file_operations_test"
        try:
            register_project_tool(path=str(project_path), name=project_name)
        except Exception:
            # If registration fails, try with a more unique name
            import time

            project_name = f"file_operations_test_{int(time.time())}"
            register_project_tool(path=str(project_path), name=project_name)

        yield {
            "name": project_name,
            "path": str(project_path),
            "files": {
                "python": "test.py",
                "text": "readme.txt",
                "empty": "empty.md",
                "nested": "nested/nested.py",
                "large": "large.log",
                "hidden_dir": ".hidden",
                "hidden_file": ".hidden/hidden.txt",
            },
        }


# Test list_project_files function
def test_list_project_files_basic(test_project):
    """Test basic functionality of list_project_files."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # List all files
    files = list_project_files(project)

    # Verify basic files are listed
    assert test_project["files"]["python"] in files
    assert test_project["files"]["text"] in files
    assert test_project["files"]["empty"] in files
    assert test_project["files"]["nested"] in files


def test_list_project_files_with_pattern(test_project):
    """Test list_project_files with a glob pattern."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # List files with pattern
    python_files = list_project_files(project, pattern="**/*.py")

    # Verify only Python files are listed
    assert test_project["files"]["python"] in python_files
    assert test_project["files"]["nested"] in python_files
    assert test_project["files"]["text"] not in python_files
    assert test_project["files"]["empty"] not in python_files


def test_list_project_files_with_max_depth(test_project):
    """Test list_project_files with max_depth parameter."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # List files with max_depth=0 (only files in root)
    root_files = list_project_files(project, max_depth=0)

    # Verify only root files are listed
    assert test_project["files"]["python"] in root_files
    assert test_project["files"]["text"] in root_files
    assert test_project["files"]["empty"] in root_files
    assert test_project["files"]["nested"] not in root_files


def test_list_project_files_with_extensions(test_project):
    """Test list_project_files with extension filtering."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # List files with specific extensions
    md_files = list_project_files(project, filter_extensions=["md"])
    text_files = list_project_files(project, filter_extensions=["txt"])
    code_files = list_project_files(project, filter_extensions=["py"])

    # Verify correct filtering
    assert test_project["files"]["empty"] in md_files
    assert test_project["files"]["text"] in text_files
    assert test_project["files"]["python"] in code_files
    assert test_project["files"]["nested"] in code_files

    # Verify no cross-contamination
    assert test_project["files"]["python"] not in md_files
    assert test_project["files"]["text"] not in code_files


# Test get_file_content function
def test_get_file_content_basic(test_project):
    """Test basic functionality of get_file_content."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Get content of Python file
    content = get_file_content(project, test_project["files"]["python"])

    # Verify content
    assert "def hello()" in content
    assert "print('Hello, world!')" in content


def test_get_file_content_empty(test_project):
    """Test get_file_content with an empty file."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Get content of empty file
    content = get_file_content(project, test_project["files"]["empty"])

    # Verify content is empty
    assert content == ""


def test_get_file_content_with_line_limits(test_project):
    """Test get_file_content with line limiting parameters."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Get content with max_lines
    content = get_file_content(project, test_project["files"]["python"], max_lines=2)

    # Verify only first two lines are returned
    assert "def hello()" in content  # Note the space - looking for function definition
    assert "print('Hello, world!')" in content
    assert "\nhello()" not in content  # Look for newline + hello() to find the function call line

    # Get content with start_line
    content = get_file_content(project, test_project["files"]["python"], start_line=2)

    # Verify only lines after start_line are returned
    assert "def hello()" not in content
    assert "hello()" in content


def test_get_file_content_nonexistent_file(test_project):
    """Test get_file_content with a nonexistent file."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Try to get content of a nonexistent file
    with pytest.raises(FileAccessError):
        get_file_content(project, "nonexistent.py")


def test_get_file_content_outside_project(test_project):
    """Test get_file_content with a path outside the project."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Try to get content of a file outside the project
    with pytest.raises(FileAccessError):
        get_file_content(project, "../outside.txt")


def test_get_file_content_as_bytes(test_project):
    """Test get_file_content with as_bytes=True."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Get content as bytes
    content = get_file_content(project, test_project["files"]["python"], as_bytes=True)

    # Verify content is bytes
    assert isinstance(content, bytes)
    assert b"def hello()" in content


# Test get_file_info function
def test_get_file_info_basic(test_project):
    """Test basic functionality of get_file_info."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Get info for Python file
    info = get_file_info(project, test_project["files"]["python"])

    # Verify info
    assert info["path"] == test_project["files"]["python"]
    assert info["size"] > 0
    assert info["is_directory"] is False
    assert info["extension"] == "py"
    assert info["line_count"] > 0


def test_get_file_info_directory(test_project):
    """Test get_file_info with a directory."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Get info for nested directory
    info = get_file_info(project, "nested")

    # Verify info
    assert info["path"] == "nested"
    assert info["is_directory"] is True
    assert info["line_count"] is None  # Line count should be None for directories


def test_get_file_info_nonexistent_file(test_project):
    """Test get_file_info with a nonexistent file."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Try to get info for a nonexistent file
    with pytest.raises(FileAccessError):
        get_file_info(project, "nonexistent.py")


def test_get_file_info_outside_project(test_project):
    """Test get_file_info with a path outside the project."""
    # Get project object
    from mcp_server_tree_sitter.api import get_project_registry

    project_registry = get_project_registry()
    project = project_registry.get_project(test_project["name"])

    # Try to get info for a file outside the project
    with pytest.raises(FileAccessError):
        get_file_info(project, "../outside.txt")


# Test count_lines function
def test_count_lines(test_project):
    """Test the count_lines function."""
    # Get absolute path to Python file
    python_file_path = Path(test_project["path"]) / test_project["files"]["python"]

    # Count lines
    line_count = count_lines(python_file_path)

    # Verify line count
    assert line_count == 4  # Based on the file content we created


def test_count_lines_empty_file(test_project):
    """Test count_lines with an empty file."""
    # Get absolute path to empty file
    empty_file_path = Path(test_project["path"]) / test_project["files"]["empty"]

    # Count lines
    line_count = count_lines(empty_file_path)

    # Verify line count
    assert line_count == 0


def test_count_lines_large_file(test_project):
    """Test count_lines with a large file."""
    # Get absolute path to large file
    large_file_path = Path(test_project["path"]) / test_project["files"]["large"]

    # Count lines
    line_count = count_lines(large_file_path)

    # Verify line count
    assert line_count == 1000  # Based on the file content we created
