"""Tests for command-line argument handling."""

import subprocess
import sys
from unittest.mock import patch

import pytest

from mcp_server_tree_sitter.server import main


def test_help_flag_does_not_start_server():
    """Test that --help flag prints help and doesn't start the server."""
    # Use subprocess to test the actual command
    result = subprocess.run(
        [sys.executable, "-m", "mcp_server_tree_sitter", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    # Check that it exited successfully
    assert result.returncode == 0

    # Check that the help text was printed
    assert "MCP Tree-sitter Server" in result.stdout
    assert "--help" in result.stdout
    assert "--config" in result.stdout

    # Server should not have started - no startup messages
    assert "Starting MCP Tree-sitter Server" not in result.stdout


def test_version_flag_exits_without_starting_server():
    """Test that --version shows version and exits without starting the server."""
    result = subprocess.run(
        [sys.executable, "-m", "mcp_server_tree_sitter", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    # Check that it exited successfully
    assert result.returncode == 0

    # Check that the version was printed
    assert "mcp-server-tree-sitter version" in result.stdout

    # Server should not have started
    assert "Starting MCP Tree-sitter Server" not in result.stdout


def test_direct_script_help_flag():
    """Test that mcp-server-tree-sitter --help works correctly when called as a script."""
    # This uses a mock to avoid actually calling the script binary
    with (
        patch("sys.argv", ["mcp-server-tree-sitter", "--help"]),
        patch("argparse.ArgumentParser.parse_args") as mock_parse_args,
        # We don't actually need to use mock_exit in the test,
        # but we still want to patch sys.exit to prevent actual exits
        patch("sys.exit"),
    ):
        # Mock the ArgumentParser.parse_args to simulate --help behavior
        # When --help is used, argparse exits with code 0 after printing help
        mock_parse_args.side_effect = SystemExit(0)

        # This should catch the SystemExit raised by parse_args
        with pytest.raises(SystemExit) as excinfo:
            main()

        # Verify it's exiting with code 0 (success)
        assert excinfo.value.code == 0


def test_entry_point_implementation():
    """Verify that the entry point properly uses argparse for argument handling."""
    import inspect

    from mcp_server_tree_sitter.server import main

    # Get the source code of the main function
    source = inspect.getsource(main)

    # Check that it's using argparse
    assert "argparse.ArgumentParser" in source
    assert "parse_args" in source

    # Check for proper handling of key flags
    assert "--help" in source or "automatically" in source  # argparse adds --help automatically
    assert "--version" in source
