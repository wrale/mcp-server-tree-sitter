# MCP Tree-sitter Server Configuration Guide

This document explains the configuration system for the MCP Tree-sitter Server, including both the YAML configuration format and the internal architecture changes for configuration management.

## YAML Configuration Format

The MCP Tree-sitter Server can be configured using a YAML file with the following sections:

### Cache Settings

Controls the parser tree cache behavior:

```yaml
cache:
  enabled: true                # Enable/disable caching (default: true)
  max_size_mb: 100             # Maximum cache size in MB (default: 100)
  ttl_seconds: 300             # Cache entry time-to-live in seconds (default: 300)
```

### Security Settings

Controls security boundaries:

```yaml
security:
  max_file_size_mb: 5          # Maximum file size to process in MB (default: 5)
  excluded_dirs:               # Directories to exclude from processing
    - .git
    - node_modules
    - __pycache__
  allowed_extensions:          # Optional list of allowed file extensions
    # - py
    # - js
    # - ts
    # Leave empty or omit for all extensions
```

### Language Settings

Controls language behavior:

```yaml
language:
  auto_install: false          # DEPRECATED: No longer used with tree-sitter-language-pack
  default_max_depth: 5         # Default max depth for AST traversal (default: 5)
  preferred_languages:         # List of languages to pre-load at server startup for improved performance
    - python                   # Pre-loading reduces latency for first operations
    - javascript
    - typescript
```

### General Settings

Controls general server behavior:

```yaml
log_level: INFO               # General logging level (DEBUG, INFO, WARNING, ERROR)
max_results_default: 100      # Default maximum results for search operations
```

### Complete Example

Here's a complete example configuration file:

```yaml
cache:
  enabled: true
  max_size_mb: 256
  ttl_seconds: 3600

security:
  max_file_size_mb: 10
  excluded_dirs:
    - .git
    - node_modules
    - __pycache__
    - .cache
    - .venv
    - vendor
  allowed_extensions:
    - py
    - js
    - ts
    - rs
    - go

language:
  default_max_depth: 7
  preferred_languages:
    - python         # Pre-load these language parsers at startup
    - javascript      # for faster initial performance
    - typescript

log_level: INFO
max_results_default: 100
```

## Deprecated Settings

The following settings are deprecated and should not be used in new configurations:

```yaml
language:
  auto_install: true  # DEPRECATED: No longer used with tree-sitter-language-pack
```

This setting was used to control automatic installation of language parsers, but it's no longer relevant since the server now uses tree-sitter-language-pack which includes all supported languages.

## Language Settings: preferred_languages

The `preferred_languages` setting allows you to specify which language parsers should be pre-loaded at server startup:

```yaml
language:
  preferred_languages:
    - python
    - javascript
    - typescript
```

**Purpose and benefits:**

- **Performance improvement**: Pre-loading parsers avoids the latency of loading them on first use
- **Early error detection**: Any issues with parsers are detected at startup, not during operation
- **Predictable memory usage**: Memory for parsers is allocated upfront

By default, this list is empty and parsers are loaded on-demand when first needed. For best performance, specify the languages you plan to use most frequently in your projects.

## Configuration Architecture

### Dependency Injection Approach

The MCP Tree-sitter Server uses a dependency injection (DI) pattern for configuration management. This is implemented with a central container and a global context that serve as structured access points. This approach improves:

- **Testability**: Components can be tested with mock configurations
- **Thread safety**: Configuration access is centralized with proper locking
- **Modularity**: Components are decoupled from direct global variable access

While the system does use singleton objects internally, they are accessed through proper dependency injection patterns rather than direct global variable usage.

### Key Components

#### Dependency Container

The central component is the `DependencyContainer` which holds all shared services:

```python
from mcp_server_tree_sitter.di import get_container

# Get the global container instance
container = get_container()

# Access services
config_manager = container.config_manager
project_registry = container.project_registry
language_registry = container.language_registry
tree_cache = container.tree_cache
```

#### ServerContext

The `ServerContext` provides a convenient high-level interface to the container:

```python
from mcp_server_tree_sitter.context import ServerContext, global_context

# Use the global context instance
config = global_context.get_config()

# Or create a custom context for testing
test_context = ServerContext()
test_config = test_context.get_config()
```

#### API Functions

The most convenient way to access functionality is through API functions:

```python
from mcp_server_tree_sitter.api import get_config, get_language_registry, register_project

# Access services through API functions
config = get_config()
language_registry = get_language_registry()
project = register_project("/path/to/project")
```

### Global Context vs. Pure Dependency Injection

The server provides multiple approaches to accessing services:

1. **API Functions**: For simplicity and convenience, most code should use these functions
2. **Dependency Container**: For more control, access the container directly
3. **Global Context**: A higher-level interface to the container
4. **Pure DI**: For testing, components can accept explicit dependencies as parameters

Example of pure DI:

```python
def configure_with_context(context, config_path=None, cache_enabled=None, ...):
    # Use the provided context rather than global state
    result, config = context.config_manager.load_from_file(config_path)
    return result, config
```

## Configuring the Server

### Using the MCP Tool

Use the `configure` MCP tool to apply configuration:

```python
# Load from YAML file
configure(config_path="/path/to/config.yaml")

# Set specific values
configure(cache_enabled=True, max_file_size_mb=10, log_level="DEBUG")
```

### Using Environment Variables

Set environment variables to configure the server:

```sh
# Set cache size
export MCP_TS_CACHE_MAX_SIZE_MB=256

# Set log level
export MCP_TS_LOG_LEVEL=DEBUG

# Set config file path 
export MCP_TS_CONFIG_PATH=/path/to/config.yaml

# Run the server
mcp run mcp_server_tree_sitter.server
```

Environment variables use the format `MCP_TS_SECTION_SETTING` where:
- `MCP_TS_` is the required prefix for all environment variables
- `SECTION` corresponds to a configuration section (e.g., `CACHE`, `SECURITY`, `LANGUAGE`)
- `SETTING` corresponds to a specific setting within that section (e.g., `MAX_SIZE_MB`, `MAX_FILE_SIZE_MB`)

For top-level settings like `log_level`, the format is simply `MCP_TS_SETTING` (e.g., `MCP_TS_LOG_LEVEL`).

#### Configuration Precedence

The server follows this precedence order when determining configuration values:

1. **Environment Variables** (highest precedence)
2. **Explicit Updates** via `update_value()`
3. **YAML Configuration** from file
4. **Default Values** (lowest precedence)

This means environment variables will always override values from other sources.

##### Reasoning for this Precedence Order

This precedence model was chosen for several important reasons:

1. **Containerization compatibility**: Environment variables are the standard way to configure applications in containerized environments like Docker and Kubernetes. Having them at the highest precedence ensures compatibility with modern deployment practices.

2. **Operational control**: System administrators and DevOps teams can set environment variables to enforce certain behaviors without worrying about code accidentally or intentionally overriding those settings.

3. **Security boundaries**: Critical security settings like `max_file_size_mb` are better protected when environment variables take precedence, creating a hard boundary that code cannot override.

4. **Debugging convenience**: Setting `MCP_TS_LOG_LEVEL=DEBUG` should reliably increase logging verbosity regardless of other configuration sources, making troubleshooting easier.

5. **Runtime adjustability**: Having explicit updates second in precedence allows for runtime configuration changes that don't persist beyond the current session, unlike environment variables which might be set system-wide.

6. **Fallback clarity**: With this model, it's clear that YAML provides the persistent configuration and defaults serve as the ultimate fallback, leading to predictable behavior.

## Default Configuration Locations

The server will look for configuration files in the following locations:

1. Path specified by `MCP_TS_CONFIG_PATH` environment variable
2. Default location: `~/.config/tree-sitter/config.yaml`

## Best Practices

### For Server Users

1. Create a `.treesitter.yaml` file in your project root with your preferred settings
2. Use the `configure` MCP tool with the path to your YAML file
3. Adjust cache size based on your project size and available memory

### For Server Developers

1. Use API functions for most operations
2. Use dependency injection with explicit parameters for new code
3. Access the dependency container directly only when necessary
4. Write tests with isolated contexts rather than relying on global state

## Migration from Global CONFIG

If you have code that previously used the global `CONFIG` variable directly, update it as follows:

**Old code:**
```python
from mcp_server_tree_sitter.config import CONFIG

max_depth = CONFIG.language.default_max_depth
```

**New code:**
```python
from mcp_server_tree_sitter.api import get_config

config = get_config()
max_depth = config.language.default_max_depth
```

### Importing Exceptions

With the dependency injection approach, exceptions must be imported explicitly. For example, if using `SecurityError` or `FileAccessError`:

```python
from mcp_server_tree_sitter.exceptions import SecurityError, FileAccessError

# Now you can use these exceptions in your code
```

For tests, create isolated contexts:

```python
from mcp_server_tree_sitter.context import ServerContext
from mcp_server_tree_sitter.config import ConfigurationManager

# Create test context
config_manager = ConfigurationManager()
config_manager.update_value("cache.enabled", False)
test_context = ServerContext(config_manager=config_manager)

# Use test context in your function
result = my_function(context=test_context)
```
