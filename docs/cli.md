# MCP Tree-sitter Server CLI Guide

This document explains the command-line interface (CLI) for the MCP Tree-sitter Server, including available options and usage patterns.

## Command-Line Arguments

The MCP Tree-sitter Server provides a command-line interface with several options:

```bash
mcp-server-tree-sitter [options]
```

### Available Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version information and exit |
| `--config CONFIG` | Path to configuration file |
| `--debug` | Enable debug logging |
| `--disable-cache` | Disable parse tree caching |

### Examples

Display help information:
```bash
mcp-server-tree-sitter --help
```

Show version information:
```bash
mcp-server-tree-sitter --version
```

Run with a custom configuration file:
```bash
mcp-server-tree-sitter --config /path/to/config.yaml
```

Enable debug logging:
```bash
mcp-server-tree-sitter --debug
```

Disable parse tree caching:
```bash
mcp-server-tree-sitter --disable-cache
```

## Running with MCP

The server can also be run using the MCP command-line interface:

```bash
# Run the server
mcp run mcp_server_tree_sitter.server

# Run with the MCP Inspector
mcp dev mcp_server_tree_sitter.server
```

You can pass the same arguments to these commands:

```bash
# Enable debug logging
mcp run mcp_server_tree_sitter.server --debug

# Use a custom configuration file with the inspector
mcp dev mcp_server_tree_sitter.server --config /path/to/config.yaml
```

## Using Makefile Targets

For convenience, the project provides Makefile targets for common operations:

```bash
# Show available targets
make

# Run the server with default settings
make mcp-run

# Run with specific arguments
make mcp-run ARGS="--debug --config /path/to/config.yaml"

# Run with the inspector
make mcp-dev ARGS="--debug"
```

## Environment Variables

The server also supports configuration through environment variables:

```bash
# Set log level
export MCP_TS_LOG_LEVEL=DEBUG

# Set configuration file path
export MCP_TS_CONFIG_PATH=/path/to/config.yaml

# Run the server
mcp-server-tree-sitter
```

See the [Configuration Guide](./config.md) for more details on environment variables and configuration options.
