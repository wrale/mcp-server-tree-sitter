# Architecture Overview

This document provides an overview of the MCP Tree-sitter Server's architecture, focusing on key components and design patterns.

## Core Architecture

The MCP Tree-sitter Server follows a structured architecture with the following components:

1. **Bootstrap Layer**: Core initialization systems that must be available to all modules with minimal dependencies
2. **Configuration Layer**: Configuration management with environment variable support
3. **Dependency Injection Container**: Central container for managing and accessing services
4. **Tree-sitter Integration**: Interfaces with the tree-sitter library for parsing and analysis
5. **MCP Protocol Layer**: Handles interactions with the Model Context Protocol

## Bootstrap Layer

The bootstrap layer handles critical initialization tasks that must happen before anything else:

```
src/mcp_server_tree_sitter/bootstrap/
├── __init__.py           # Exports key bootstrap functions
└── logging_bootstrap.py  # Canonical logging configuration
```

This layer is imported first in the package's `__init__.py` and has minimal dependencies. The bootstrap module ensures that core services like logging are properly initialized and globally available to all modules.

**Key Design Principle**: Each component in the bootstrap layer must have minimal dependencies to avoid import cycles and ensure reliable initialization.

## Dependency Injection Pattern

Instead of using global variables (which was the approach in earlier versions), the application now uses a structured dependency injection pattern:

1. **DependencyContainer**: The `DependencyContainer` class holds all application components and services
2. **ServerContext**: A context class provides a clean interface for interacting with dependencies
3. **Access Functions**: API functions like `get_logger()` and `update_log_levels()` provide easy access to functionality

This approach has several benefits:
- Cleaner testing with the ability to mock dependencies
- Better encapsulation of implementation details
- Reduced global state and improved thread safety
- Clearer dependency relationships between components

## Logging Design

Logging follows a hierarchical model using Python's standard `logging` module:

1. **Root Package Logger**: Only the root package logger (`mcp_server_tree_sitter`) has its level explicitly set
2. **Child Loggers**: Child loggers inherit their level from the root package logger
3. **Handler Synchronization**: Handler levels are synchronized with their logger's effective level

**Canonical Implementation**: The logging system is defined in a single location - `bootstrap/logging_bootstrap.py`. Other modules import from this module to ensure consistent behavior.

### Logging Functions

The bootstrap module provides these key logging functions:

```python
# Get log level from environment variable
get_log_level_from_env()

# Configure the root logger
configure_root_logger()

# Get a properly configured logger
get_logger(name)

# Update log levels
update_log_levels(level_name)
```

## Configuration System

The configuration system uses a layered approach:

1. **Environment Variables**: Highest precedence (e.g., `MCP_TS_LOG_LEVEL=DEBUG`)
2. **Explicit Updates**: Updates made via `update_value()` calls
3. **YAML Configuration**: Settings from YAML configuration files
4. **Default Values**: Fallback defaults defined in model classes

The `ConfigurationManager` is responsible for loading, managing, and applying configuration, while a `ServerConfig` model encapsulates the actual configuration settings.

## Project and Language Management

Projects and languages are managed by registry classes:

1. **ProjectRegistry**: Maintains active project registrations
2. **LanguageRegistry**: Manages tree-sitter language parsers

These registries are accessed through the dependency container or context, providing a clean interface for operations.

## Use of Builder and Factory Patterns

The server uses several design patterns for cleaner code:

1. **Builder Pattern**: Used for constructing complex objects like `Project` instances
2. **Factory Methods**: Used to create tree-sitter parsers and queries
3. **Singleton Pattern**: Used for the dependency container to ensure consistent state

## Lifecycle Management

The server's lifecycle is managed in a structured way:

1. **Bootstrap Phase**: Initializes logging and critical systems (from `__init__.py`)
2. **Configuration Phase**: Loads configuration from files and environment
3. **Dependency Initialization**: Sets up all dependencies in the container
4. **Server Setup**: Configures MCP tools and capabilities
5. **Running Phase**: Processes requests from the MCP client
6. **Shutdown**: Gracefully handles shutdown and cleanup

## Error Handling Strategy

The server implements a layered error handling approach:

1. **Custom Exceptions**: Defined in `exceptions.py` for specific error cases
2. **Function-Level Handlers**: Most low-level functions do error handling
3. **Tool-Level Handlers**: MCP tools handle errors and return structured responses
4. **Global Exception Handling**: FastMCP provides top-level error handling

## Future Architecture Improvements

Planned architectural improvements include:

1. **Complete Decoupling**: Further reduce dependencies between components
2. **Module Structure Refinement**: Better organize modules by responsibility
3. **Configuration Caching**: Optimize configuration access patterns
4. **Async Support**: Add support for asynchronous operations
5. **Plugin Architecture**: Support for extensibility through plugins
