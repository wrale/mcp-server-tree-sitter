# MCP Tree-sitter Server

A Model Context Protocol (MCP) server that provides code analysis capabilities using tree-sitter, designed to give Claude intelligent access to codebases with appropriate context management.

<a href="https://glama.ai/mcp/servers/@wrale/mcp-server-tree-sitter">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@wrale/mcp-server-tree-sitter/badge" alt="mcp-server-tree-sitter MCP server" />
</a>

## Features

- 🔍 **Flexible Exploration**: Examine code at multiple levels of granularity
- 🧠 **Context Management**: Provides just enough information without overwhelming the context window
- 🌐 **Language Agnostic**: Supports many programming languages including Python, JavaScript, TypeScript, Go, Rust, C, C++, Swift, Java, Kotlin, Julia, and APL via tree-sitter-language-pack
- 🌳 **Structure-Aware**: Uses AST-based understanding with efficient cursor-based traversal
- 🔎 **Searchable**: Find specific patterns using text search and tree-sitter queries
- 🔄 **Caching**: Optimized performance through parse tree caching
- 🔑 **Symbol Extraction**: Extract and analyze functions, classes, and other code symbols
- 📊 **Dependency Analysis**: Identify and analyze code dependencies and relationships
- 🧩 **State Persistence**: Maintains project registrations and cached data between invocations
- 🔒 **Secure**: Built-in security boundaries and input validation

For a comprehensive list of all available commands, their current implementation status, and detailed feature matrix, please refer to the [FEATURES.md](FEATURES.md) document.

## Installation

### Prerequisites

- Python 3.10+
- Tree-sitter language parsers for your preferred languages

### Basic Installation

```bash
pip install mcp-server-tree-sitter
```

### Development Installation

```bash
git clone https://github.com/wrale/mcp-server-tree-sitter.git
cd mcp-server-tree-sitter
pip install -e ".[dev,languages]"
```

## Quick Start

### Running with Claude Desktop

You can make the server available in Claude Desktop either through the MCP CLI or by manually configuring Claude Desktop.

#### Using MCP CLI

Register the server with Claude Desktop:

```bash
mcp install mcp_server_tree_sitter.server:mcp --name "tree_sitter"
```

#### Manual Configuration

Alternatively, you can manually configure Claude Desktop:

1. Open your Claude Desktop configuration file:
   - macOS/Linux: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   
   Create the file if it doesn't exist.

2. Add the server to the `mcpServers` section:

   ```json
   {
       "mcpServers": {
           "tree_sitter": {
               "command": "python",
               "args": [
                   "-m",
                   "mcp_server_tree_sitter.server"
               ]
           }
       }
   }
   ```

   Alternatively, if using uv or another package manager:

   ```json
   {
       "mcpServers": {
           "tree_sitter": {
               "command": "uv",
               "args": [
                   "--directory",
                   "/ABSOLUTE/PATH/TO/YOUR/PROJECT",
                   "run",
                   "-m",
                   "mcp_server_tree_sitter.server"
               ]
           }
       }
   }
   ```

   Note: Make sure to replace `/ABSOLUTE/PATH/TO/YOUR/PROJECT` with the actual absolute path to your project directory.

3. Save the file and restart Claude Desktop.

The MCP tools icon (hammer) will appear in Claude Desktop's interface once you have properly configured at least one MCP server. You can then access the `tree_sitter` server's functionality by clicking on this icon.

### Configuring with Released Version

If you prefer not to manually install the package from PyPI (released version) or clone the repository, simply use the following configuration for Claude Desktop:

1. Open your Claude Desktop configuration file (same location as above).

2. Add the tree-sitter server to the `mcpServers` section:

   ```json
   {
       "mcpServers": {
           "tree_sitter": {
               "command": "uvx",
               "args": [
                   "--directory", "/ABSOLUTE/PATH/TO/YOUR/PROJECT",
                   "mcp-server-tree-sitter"
               ]
           }
       }
   }
   ```

3. Save the file and restart Claude Desktop.

This method uses `uvx` to run the installed PyPI package directly, which is the recommended approach for the released version. The server doesn't require any additional parameters to run in its basic configuration.

## State Persistence

The MCP Tree-sitter Server maintains state between invocations. This means:
- Projects stay registered until explicitly removed or the server is restarted
- Parse trees are cached according to configuration settings
- Language information is retained throughout the server's lifetime

This persistence is maintained in-memory during the server's lifetime using singleton patterns for key components.

### Running as a standalone server

```bash
mcp run mcp_server_tree_sitter.server
```

### Using with the MCP Inspector

```bash
mcp dev mcp_server_tree_sitter.server
```

## Usage

### Register a Project

First, register a project to analyze:

```
register_project_tool(path="/path/to/your/project", name="my-project")
```

### Explore Files

List files in the project:

```
list_files(project="my-project", pattern="**/*.py")
```

View file content:

```
get_file(project="my-project", path="src/main.py")
```

### Analyze Code Structure

Get the syntax tree:

```
get_ast(project="my-project", path="src/main.py", max_depth=3)
```

Extract symbols:

```
get_symbols(project="my-project", path="src/main.py")
```

### Search Code

Search for text:

```
find_text(project="my-project", pattern="function", file_pattern="**/*.py")
```

Run tree-sitter queries:

```
run_query(
    project="my-project",
    query='(function_definition name: (identifier) @function.name)',
    language="python"
)
```

### Analyze Complexity

```
analyze_complexity(project="my-project", path="src/main.py")
```

## Direct Python Usage

While the primary intended use is through the MCP server, you can also use the library directly in Python code:

```python
# Import from the API module
from mcp_server_tree_sitter.api import (
    register_project, list_projects, get_config, get_language_registry
)

# Register a project
project_info = register_project(
    path="/path/to/project", 
    name="my-project", 
    description="Description"
)

# List projects
projects = list_projects()

# Get configuration
config = get_config()

# Access components through dependency injection
from mcp_server_tree_sitter.di import get_container
container = get_container()
project_registry = container.project_registry
language_registry = container.language_registry
```

## Configuration

Create a YAML configuration file:

```yaml
cache:
  enabled: true                # Enable/disable caching (default: true)
  max_size_mb: 100             # Maximum cache size in MB (default: 100)
  ttl_seconds: 300             # Cache entry time-to-live in seconds (default: 300)

security:
  max_file_size_mb: 5          # Maximum file size to process in MB (default: 5)
  excluded_dirs:               # Directories to exclude from processing
    - .git
    - node_modules
    - __pycache__
  allowed_extensions:          # Optional list of allowed file extensions
    # - py
    # - js
    # Leave empty or omit for all extensions

language:
  default_max_depth: 5         # Default max depth for AST traversal (default: 5)
  preferred_languages:         # List of languages to pre-load at startup for faster performance
    - python                   # Pre-loading reduces latency for first operations
    - javascript

log_level: INFO                # Logging level (DEBUG, INFO, WARNING, ERROR)
max_results_default: 100       # Default maximum results for search operations
```

Load it with:

```
configure(config_path="/path/to/config.yaml")
```

### About preferred_languages

The `preferred_languages` setting controls which language parsers are pre-loaded at server startup rather than on-demand. This provides several benefits:

- **Faster initial analysis**: No delay when first analyzing a file of a pre-loaded language
- **Early error detection**: Issues with parsers are discovered at startup, not during use
- **Predictable memory allocation**: Memory for frequently used parsers is allocated upfront

By default, all parsers are loaded on-demand when first needed. For optimal performance, specify the languages you use most frequently in your projects.

You can also configure specific settings:

```
configure(cache_enabled=True, max_file_size_mb=10, log_level="DEBUG")
```

Or use environment variables:

```bash
export MCP_TS_CACHE_MAX_SIZE_MB=256
export MCP_TS_LOG_LEVEL=DEBUG
export MCP_TS_CONFIG_PATH=/path/to/config.yaml
```

The server will look for configuration in:
1. Path specified in `configure()` call
2. Path specified by `MCP_TS_CONFIG_PATH` environment variable
3. Default location: `~/.config/tree-sitter/config.yaml`

## Available Resources

The server provides the following MCP resources:

- `project://{project}/files` - List all files in a project
- `project://{project}/files/{pattern}` - List files matching a pattern
- `project://{project}/file/{path}` - Get file content
- `project://{project}/file/{path}/lines/{start}-{end}` - Get specific lines from a file
- `project://{project}/ast/{path}` - Get the AST for a file
- `project://{project}/ast/{path}/depth/{depth}` - Get the AST with custom depth

## Available Tools

The server provides tools for:

- Project management: `register_project_tool`, `list_projects_tool`, `remove_project_tool`
- Language management: `list_languages`, `check_language_available`
- File operations: `list_files`, `get_file`, `get_file_metadata`
- AST analysis: `get_ast`, `get_node_at_position`
- Code search: `find_text`, `run_query`
- Symbol extraction: `get_symbols`, `find_usage`
- Project analysis: `analyze_project`, `get_dependencies`, `analyze_complexity`
- Query building: `get_query_template_tool`, `list_query_templates_tool`, `build_query`, `adapt_query`, `get_node_types`
- Similar code detection: `find_similar_code`
- Cache management: `clear_cache`
- Configuration diagnostics: `diagnose_config`

See [FEATURES.md](FEATURES.md) for detailed information about each tool's implementation status, dependencies, and usage examples.

## Available Prompts

The server provides the following MCP prompts:

- `code_review` - Create a prompt for reviewing code
- `explain_code` - Create a prompt for explaining code
- `explain_tree_sitter_query` - Explain tree-sitter query syntax
- `suggest_improvements` - Create a prompt for suggesting code improvements
- `project_overview` - Create a prompt for a project overview analysis

## License

MIT