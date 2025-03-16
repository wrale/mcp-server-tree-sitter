# MCP Tree-sitter Server

A Model Context Protocol (MCP) server that provides code analysis capabilities using tree-sitter, designed to give Claude intelligent access to codebases with appropriate context management.

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

## Configuration

Create a YAML configuration file:

```yaml
cache:
  enabled: true
  max_size_mb: 100
  ttl_seconds: 300

security:
  max_file_size_mb: 5
  excluded_dirs:
    - .git
    - node_modules
    - __pycache__

language:
  auto_install: false
  default_max_depth: 5
```

Load it with:

```
configure(config_path="/path/to/config.yaml")
```

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
- Query building: `get_query_template_tool`, `list_query_templates_tool`, `build_query`, `adapt_query`
- Cache management: `clear_cache`

## Available Prompts

The server provides the following MCP prompts:

- `code_review` - Create a prompt for reviewing code
- `explain_code` - Create a prompt for explaining code
- `explain_tree_sitter_query` - Explain tree-sitter query syntax
- `suggest_improvements` - Create a prompt for suggesting code improvements
- `project_overview` - Create a prompt for a project overview analysis

## License

MIT
