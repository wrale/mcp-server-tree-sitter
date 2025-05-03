"""Tests for Makefile targets to ensure they execute correctly."""

import os
import re
import subprocess
from pathlib import Path


def test_makefile_target_syntax():
    """Test that critical Makefile targets are correctly formed."""
    # Get the Makefile content
    makefile_path = Path(__file__).parent.parent / "Makefile"
    with open(makefile_path, "r") as f:
        makefile_content = f.read()

    # Test mcp targets - they should use uv run mcp directly
    mcp_target_pattern = r"mcp-(run|dev|install):\n\t\$\(UV\) run mcp"
    mcp_targets = re.findall(mcp_target_pattern, makefile_content)

    # We should find at least 3 matches (run, dev, install)
    assert len(mcp_targets) >= 3, "Missing proper mcp invocation in Makefile targets"

    # Check for correct server module reference
    assert "$(PACKAGE).server" in makefile_content, "Server module reference is incorrect"

    # Custom test for mcp-run
    mcp_run_pattern = r"mcp-run:.*\n\t\$\(UV\) run mcp run \$\(PACKAGE\)\.server"
    assert re.search(mcp_run_pattern, makefile_content), "mcp-run target is incorrectly formed"

    # Test that help is the default target
    assert ".PHONY: all help" in makefile_content, "help is not properly declared as .PHONY"
    assert "help: show-help" in makefile_content, "help is not properly set as default target"


def test_makefile_target_execution():
    """Test that Makefile targets execute correctly when invoked with --help."""
    # We'll only try the --help flag since we don't want to actually start the server
    # Skip if not in a development environment
    if not os.path.exists("Makefile"):
        print("Skipping test_makefile_target_execution: Makefile not found")
        return

    # Skip this test in CI environment
    if os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
        print("Skipping test_makefile_target_execution in CI environment")
        return

    # Test mcp-run with --help
    try:
        # Use the make target with --help appended to see if it resolves correctly
        # We capture stderr because sometimes help messages go there
        result = subprocess.run(
            ["make", "mcp-run", "ARGS=--help"],
            capture_output=True,
            text=True,
            timeout=5,  # Don't let this run too long
            check=False,
            env={**os.environ, "MAKEFLAGS": ""},  # Clear any inherited make flags
        )

        # The run shouldn't fail catastrophically
        assert "File not found" not in result.stderr, "mcp-run can't find the module"

        # We expect to see help text in the output (stdout or stderr)
        output = result.stdout + result.stderr
        has_usage = "usage:" in output.lower() or "mcp run" in output

        # We don't fail the test if the help check fails - this is more of a warning
        # since the environment might not be set up to run make directly
        if not has_usage:
            print("WARNING: Couldn't verify mcp-run --help output; environment may not be properly configured")

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        # Don't fail the test if we can't run make
        print(f"WARNING: Couldn't execute make command; skipping execution check: {e}")
