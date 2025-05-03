# Logging Configuration Guide

This document explains how logging is configured in the MCP Tree-sitter Server and how to control log verbosity using environment variables.

## Environment Variable Configuration

The simplest way to control logging verbosity is by setting the `MCP_TS_LOG_LEVEL` environment variable:

```bash
# Enable detailed debug logging
export MCP_TS_LOG_LEVEL=DEBUG

# Use normal informational logging
export MCP_TS_LOG_LEVEL=INFO

# Only show warning and error messages
export MCP_TS_LOG_LEVEL=WARNING
```

## Log Level Values

The following log level values are supported:

| Level | Description |
|-------|-------------|
| DEBUG | Most verbose, includes detailed diagnostic information |
| INFO | Standard informational messages |
| WARNING | Only warning and error messages |
| ERROR | Only error messages |
| CRITICAL | Only critical failures |

## How Logging Is Configured

The logging system follows these principles:

1. **Early Environment Variable Processing**: Environment variables are processed at the earliest point in the application lifecycle
2. **Root Logger Configuration**: The package root logger (`mcp_server_tree_sitter`) is configured based on the environment variable value
3. **Logger Hierarchy**: Levels are set _only_ on the root package logger, allowing child loggers to inherit properly
4. **Handler Synchronization**: Handler levels are synchronized to match their logger's effective level
5. **Consistent Propagation**: Log record propagation is preserved throughout the hierarchy

## Using Loggers in Code

When adding logging to code, use the centralized utility function:

```python
from mcp_server_tree_sitter.bootstrap import get_logger

# Create a properly configured logger
logger = get_logger(__name__)

# Use standard logging methods
logger.debug("Detailed diagnostic information")
logger.info("Standard information")
logger.warning("Warning message")
logger.error("Error message")
```

> **Note**: For backwards compatibility, you can also import from `mcp_server_tree_sitter.logging_config`, but new code should use the bootstrap module directly.

The `get_logger()` function respects the logger hierarchy and only sets explicit levels on the root package logger, allowing proper level inheritance for all child loggers.

## Dynamically Changing Log Levels

Log levels can be updated at runtime using:

```python
from mcp_server_tree_sitter.bootstrap import update_log_levels

# Set to debug level
update_log_levels("DEBUG")

# Or use numeric values
import logging
update_log_levels(logging.INFO)
```

This will update _only_ the root package logger and its handlers while maintaining the proper logger hierarchy. Child loggers will automatically inherit the new level.

> **Note**: You can also import these functions from `mcp_server_tree_sitter.logging_config`, which forwards to the bootstrap module for backwards compatibility.

## Command-line Configuration

When running the server directly, you can use the `--debug` flag:

```bash
python -m mcp_server_tree_sitter --debug
```

This flag sets the log level to DEBUG both via environment variable and direct configuration, ensuring consistent behavior.

## Persistence of Log Levels

Log level changes persist through the current server session, but environment variables must be set before the server starts to ensure they are applied from the earliest initialization point. Environment variables always take highest precedence in the configuration hierarchy.

## How Logger Hierarchy Works

The package uses a proper hierarchical logger structure following Python's best practices:

- `mcp_server_tree_sitter` (root package logger) - **only logger with explicitly set level**
  - `mcp_server_tree_sitter.config` (module logger) - **inherits level from parent**
  - `mcp_server_tree_sitter.server` (module logger) - **inherits level from parent**
  - etc.

### Level Inheritance

In Python's logging system:
- Each logger maintains its own level setting
- Child loggers inherit levels from parent loggers **unless** explicitly set
- Log **records** (not levels) propagate up the hierarchy if `propagate=True`
- The effective level of a logger is determined by its explicit level, or if not set, its nearest ancestor with an explicit level

Setting `MCP_TS_LOG_LEVEL=DEBUG` sets the root package logger's level to DEBUG, which affects all child loggers that don't have explicit levels. Our implementation strictly adheres to this principle and avoids setting individual logger levels unnecessarily.

### Handler vs. Logger Levels

There are two separate level checks in the logging system:

1. **Logger Level**: Determines if a message is processed by the logger
2. **Handler Level**: Determines if a processed message is output by a specific handler

Our system synchronizes handler levels with their corresponding logger's effective level (which may be inherited). This ensures that messages that pass the logger level check also pass the handler level check.

## Troubleshooting

If logs are not appearing at the expected level:

1. Ensure the environment variable is set before starting the server
2. Verify the log level was applied to the root package logger (`mcp_server_tree_sitter`)
3. Check that handler levels match their logger's effective level
4. Verify that log record propagation is enabled (`propagate=True`)
5. Use `logger.getEffectiveLevel()` to check the actual level being used by any logger
6. Remember that environment variables have the highest precedence in the configuration hierarchy

## Implementation Details

The logging system follows strict design requirements:

1. **Environment Variable Processing**: Environment variables are processed at the earliest point in the application lifecycle, before any module imports
2. **Root Logger Configuration**: Only the package root logger has its level explicitly set
3. **Handler Synchronization**: Handler levels are synchronized with their logger's effective level
4. **Propagation Preservation**: Log record propagation is enabled for consistent behavior
5. **Centralized Configuration**: All logging is configured through the `logging_config.py` module
6. **Configuration Precedence**: Environment variables > Explicit updates > YAML config > Defaults

For the complete implementation details, see the `bootstrap/logging_bootstrap.py` module source code.

## Bootstrap Architecture

The logging system is now implemented using a bootstrap architecture for improved dependency management:

1. The canonical implementation of all logging functionality is in `bootstrap/logging_bootstrap.py`
2. This module is imported first in the package's `__init__.py` before any other modules
3. The module has minimal dependencies to avoid import cycles
4. All other modules import logging utilities from the bootstrap module

### Why Bootstrap?

The bootstrap approach solves several problems:

1. **Import Order**: Ensures logging is configured before any other modules are imported
2. **Avoiding Redundancy**: Provides a single canonical implementation of logging functionality
3. **Dependency Management**: Prevents circular imports and configuration issues
4. **Consistency**: Ensures all modules use the same logging setup

### Migration from logging_config.py

For backwards compatibility, `logging_config.py` still exists but now forwards all imports to the bootstrap module. Existing code that imports from `logging_config.py` will continue to work, but new code should import directly from the bootstrap module.

```python
# Preferred for new code
from mcp_server_tree_sitter.bootstrap import get_logger, update_log_levels

# Still supported for backwards compatibility
from mcp_server_tree_sitter.logging_config import get_logger, update_log_levels
```
