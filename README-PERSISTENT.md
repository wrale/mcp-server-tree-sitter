# Persistent MCP Tree-sitter Server

This document describes the persistent version of the MCP Tree-sitter Server, which ensures project registry persistence between MCP tool calls.

## Problem 

The original MCP Tree-sitter Server implementation had an issue where projects were correctly registered with the `register_project_tool` function, but then couldn't be found in subsequent tool calls like `list_files` or `get_file`. This happened because the `project_registry` state wasn't being properly preserved between separate MCP function invocations.

## Solution

The persistent server implementation (`persistent_server.py`) extends the original server implementation with the following changes:

1. It creates a subclass of `FastMCP` called `PersistentMCP` that maintains project registry state.
2. It copies all tools, resources, and prompts from the original server implementation.
3. It overrides the project-related tools (`register_project_tool`, `list_projects_tool`, `remove_project_tool`) to ensure they work with the persistent registry.
4. It overrides the `_execute_function` method to add additional logging and state management.

## Using the Persistent Server

To use the persistent server implementation, simply configure Claude Desktop to use the persistent version by editing your Claude Desktop configuration file:

```json
{
    "mcpServers": {
        "Code Explorer": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/YOUR/PROJECT",
                "run",
                "-m",
                "mcp_server_tree_sitter"
            ]
        }
    }
}
```

The updated `__main__.py` file now uses the persistent server implementation by default.

## Testing the Solution

Two new test files have been added to verify the solution:

1. `tests/test_project_persistence.py` - Tests the project registry persistence issue and verifies the singleton pattern works correctly.
2. `tests/test_persistent_server.py` - Tests the new persistent server implementation specifically.

You can run these tests with:

```bash
make test
```

## Implementation Details

The key insight is that the issue was not with the `ProjectRegistry` class itself (which has a properly implemented singleton pattern), but with how the MCP server's tool execution lifecycle interacts with the registry.

By creating a persistent extension of `FastMCP`, we ensure that:

1. The same `ProjectRegistry` instance is used across all tool calls
2. Projects registered through the tools are properly preserved
3. Subsequent tool calls can find and use the registered projects

This allows for a seamless workflow where users can register a project and then immediately use tools like `list_files`, `get_file`, etc. on that project without any persistence issues.
