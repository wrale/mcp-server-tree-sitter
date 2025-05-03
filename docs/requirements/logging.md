# Requirements for Correct Logging Behavior in MCP Tree-sitter Server

This document specifies the requirements for implementing correct logging behavior in the MCP Tree-sitter Server, with particular focus on ensuring that environment variables like `MCP_TS_LOG_LEVEL=DEBUG` work as expected.

## Core Requirements

### 1. Environment Variable Processing

- Environment variables MUST be processed before any logging configuration is applied
- The system MUST correctly parse `MCP_TS_LOG_LEVEL` and convert it to the appropriate numeric logging level
- Environment variable values MUST take precedence over hardcoded defaults and other configuration sources

```python
# Example of correct implementation
def get_log_level_from_env() -> int:
    env_level = os.environ.get("MCP_TS_LOG_LEVEL", "INFO").upper()
    return LOG_LEVEL_MAP.get(env_level, logging.INFO)
```

### 2. Root Logger Configuration

- `logging.basicConfig()` MUST use the level derived from environment variables
- Root logger configuration MUST happen early in the application lifecycle, before other modules are imported
- Root logger handlers MUST be configured with the same level as the logger itself

```python
# Example of correct implementation
def configure_root_logger() -> None:
    log_level = get_log_level_from_env()
    
    # Configure the root logger with proper format and level
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Ensure the root logger for our package is also set correctly
    pkg_logger = logging.getLogger("mcp_server_tree_sitter")
    pkg_logger.setLevel(log_level)
    
    # Ensure all handlers have the correct level
    for handler in logging.root.handlers:
        handler.setLevel(log_level)
    
    # Ensure propagation is preserved
    pkg_logger.propagate = True
```

### 3. Package Logger Hierarchy

- The main package logger (`mcp_server_tree_sitter`) MUST be explicitly set to the level from environment variables
- **DO NOT** explicitly set levels for all individual loggers in the hierarchy unless specifically needed
- Log record propagation MUST be preserved (default `propagate=True`) to ensure messages flow up the hierarchy
- Child loggers SHOULD inherit the effective level from their parents by default

```python
# INCORRECT approach - setting levels for all loggers
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Setting levels for all package loggers disrupts hierarchy
    if name.startswith("mcp_server_tree_sitter"):
        logger.setLevel(get_log_level_from_env())
    
    return logger

# CORRECT approach - respecting logger hierarchy
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Only set the level explicitly for the root package logger
    if name == "mcp_server_tree_sitter":
        logger.setLevel(get_log_level_from_env())
    
    return logger
```

### 4. Handler Configuration

- Every logger with handlers MUST have those handlers' levels explicitly set to match the logger level
- New handlers created during runtime MUST inherit the appropriate level setting
- Handler formatter configuration MUST be consistent to ensure uniform log output

```python
# Example of correct handler synchronization
def update_handler_levels(logger: logging.Logger, level: int) -> None:
    for handler in logger.handlers:
        handler.setLevel(level)
```

### 5. Configuration Timing

- Logging configuration MUST occur before any module imports that might create loggers
- Environment variable processing MUST happen at the earliest possible point in the application lifecycle
- Any dynamic reconfiguration MUST update both logger and handler levels simultaneously

### 6. Level Update Mechanism

- When updating log levels, the system MUST update the root package logger level
- The system MUST update handler levels to match their logger levels
- The system SHOULD preserve the propagation setting when updating loggers

```python
# Example of correct level updating
def update_log_levels(level_name: str) -> None:
    level_value = LOG_LEVEL_MAP.get(level_name.upper(), logging.INFO)
    
    # Update root package logger
    pkg_logger = logging.getLogger("mcp_server_tree_sitter")
    pkg_logger.setLevel(level_value)
    
    # Update all handlers on the package logger
    for handler in pkg_logger.handlers:
        handler.setLevel(level_value)
    
    # Update existing loggers in our package
    for name in logging.root.manager.loggerDict:
        if name == "mcp_server_tree_sitter" or name.startswith("mcp_server_tree_sitter."):
            logger = logging.getLogger(name)
            logger.setLevel(level_value)
            
            # Update all handlers for this logger
            for handler in logger.handlers:
                handler.setLevel(level_value)
            
            # Preserve propagation
            logger.propagate = True
```

## Implementation Requirements

### 7. Logging Utility Functions

- Helper functions MUST be provided for creating correctly configured loggers
- Utility functions MUST ensure consistent behavior across different modules
- These utilities MUST respect Python's logging hierarchy where each logger maintains its own level

### 8. Error Handling

- The system MUST handle invalid log level strings in environment variables gracefully
- Default fallback values MUST be used when environment variables are not set
- When importing logging utilities fails, modules SHOULD fall back to standard logging

```python
# Example of robust logger acquisition with fallback
try:
    from ..logging_config import get_logger
    logger = get_logger(__name__)
except (ImportError, AttributeError):
    # Fallback to standard logging
    import logging
    logger = logging.getLogger(__name__)
```

### 9. Module Structure

- The `logging_config.py` module MUST be designed to be imported before other modules
- The module MUST automatically configure the root logger when imported
- The module MUST provide utility functions for getting loggers and updating levels

## Documentation Requirements

### 10. Documentation

- Documentation MUST explain how to use environment variables to control logging
- Documentation MUST provide examples for common logging configuration scenarios
- Documentation MUST explain the logger hierarchy and level inheritance
- Documentation MUST clarify that log records (not levels) propagate up the hierarchy

## Testing Requirements

### 11. Testing

- Tests MUST verify that environment variables are correctly processed
- Tests MUST verify that logger levels are correctly inherited in the hierarchy
- Tests MUST verify that handler levels are synchronized with logger levels
- Tests MUST verify that log messages flow up the hierarchy as expected

## Expected Behavior

When all these requirements are satisfied, setting `MCP_TS_LOG_LEVEL=DEBUG` will properly increase log verbosity throughout the application, allowing users to see detailed debug information for troubleshooting.
