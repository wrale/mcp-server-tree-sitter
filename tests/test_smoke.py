"""Smoke tests for the MCP server.

Tests at two levels:
1. Startup tests: verify the server module imports, --help/--version work,
   and all tools register correctly (fast, no protocol)
2. Protocol test: boot the server over stdio, connect as an MCP client,
   and exercise key tools end-to-end (catches registration bugs, import
   errors, and protocol mismatches that mocked unit tests cannot)
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PYTHONPATH_ENV = {**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent / "src")}


# --- Startup tests (no protocol) ---


def test_server_help():
    """Server --help exits cleanly."""
    proc = subprocess.run(
        [sys.executable, "-m", "mcp_server_tree_sitter.server", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env=PYTHONPATH_ENV,
    )
    assert proc.returncode == 0
    assert "usage" in proc.stdout.lower() or "mcp" in proc.stdout.lower()


def test_server_version():
    """Server --version exits cleanly with version info."""
    proc = subprocess.run(
        [sys.executable, "-m", "mcp_server_tree_sitter.server", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        env=PYTHONPATH_ENV,
    )
    assert proc.returncode == 0
    assert "0." in proc.stdout or "1." in proc.stdout


def test_all_tools_registered():
    """All expected tools register on the MCP server."""
    script = (
        "from mcp_server_tree_sitter.server import mcp; "
        "from mcp_server_tree_sitter.di import get_container; "
        "from mcp_server_tree_sitter.tools.registration import register_tools; "
        "register_tools(mcp, get_container()); "
        "print('\\n'.join(sorted(mcp._tool_manager._tools.keys())))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=15,
        env=PYTHONPATH_ENV,
    )
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    tools = set(proc.stdout.strip().split("\n"))
    expected = {
        "register_project_tool",
        "list_projects_tool",
        "remove_project_tool",
        "list_languages",
        "check_language_available",
        "list_files",
        "get_file",
        "get_file_metadata",
        "get_ast",
        "get_node_at_position",
        "get_symbols",
        "run_query",
        "find_text",
        "find_usage",
        "find_similar_code",
        "get_dependencies",
        "analyze_complexity",
        "analyze_project",
        "get_query_template_tool",
        "list_query_templates_tool",
        "build_query",
        "adapt_query",
        "get_node_types",
        "clear_cache",
        "configure",
        "diagnose_config",
    }
    missing = expected - tools
    assert not missing, f"Missing tools: {missing}"


# --- Protocol test (real MCP client over stdio) ---


@pytest.mark.asyncio(loop_scope="function")
async def test_mcp_protocol_smoke():
    """Boot the server over stdio and exercise key tools via MCP protocol."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server_tree_sitter.server"],
        env=PYTHONPATH_ENV,
    )

    devnull = open(os.devnull, "w")
    try:
        async with stdio_client(server_params, errlog=devnull) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 1. list_tools returns 20+ tools
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                assert len(tool_names) >= 20, f"Expected 20+ tools, got {len(tool_names)}"

                # 2. list_languages returns languages including python
                result = await session.call_tool("list_languages", {})
                data = json.loads(result.content[0].text)
                assert "python" in data["available"]
                assert "dart" in data["available"]
                assert "csharp" in data["available"]

                # 3. check_language_available works
                result = await session.call_tool("check_language_available", {"language": "python"})
                data = json.loads(result.content[0].text)
                assert data["status"] == "success"

                # 4. Full workflow: register project -> get_symbols -> run_query -> remove
                with tempfile.TemporaryDirectory() as tmp:
                    with open(f"{tmp}/app.py", "w") as f:
                        f.write("def greet(name):\n    return f'Hello, {name}'\n\nclass App:\n    pass\n")

                    # Register
                    result = await session.call_tool("register_project_tool", {"path": tmp, "name": "smoke_test"})
                    data = json.loads(result.content[0].text)
                    assert data["name"] == "smoke_test"

                    # Get symbols
                    result = await session.call_tool("get_symbols", {"project": "smoke_test", "file_path": "app.py"})
                    data = json.loads(result.content[0].text)
                    func_names = [s["name"] for s in data.get("functions", [])]
                    class_names = [s["name"] for s in data.get("classes", [])]
                    assert "greet" in func_names
                    assert "App" in class_names

                    # Run query with compact mode
                    result = await session.call_tool(
                        "run_query",
                        {
                            "project": "smoke_test",
                            "query": "(function_definition name: (identifier) @name)",
                            "file_path": "app.py",
                            "language": "python",
                            "compact": True,
                            "capture_filter": "name",
                        },
                    )
                    data = json.loads(result.content[0].text)
                    # FastMCP may return a single dict or a list
                    if isinstance(data, dict):
                        item = data
                    elif isinstance(data, list):
                        item = data[0]
                    else:
                        item = data.get("result", [data])[0]
                    assert item["capture"] == "name"
                    assert item["text"] == "greet"
                    # Compact mode should not have start/end keys
                    assert "start" not in item

                    # Clean up
                    await session.call_tool("remove_project_tool", {"name": "smoke_test"})
    finally:
        devnull.close()
