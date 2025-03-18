# MCP Tree-sitter Server: Feature Matrix

This document provides a comprehensive overview of all MCP Tree-sitter server commands, their status, dependencies, and common usage patterns. It serves as both a reference guide and a test matrix for ongoing development.

## Table of Contents
- [Supported Languages](#supported-languages)
- [Command Status Legend](#command-status-legend)
- [Command Reference](#command-reference)
  - [Project Management Commands](#project-management-commands)
  - [Language Tools Commands](#language-tools-commands)
  - [File Operations Commands](#file-operations-commands)
  - [AST Analysis Commands](#ast-analysis-commands)
  - [Search and Query Commands](#search-and-query-commands)
  - [Code Analysis Commands](#code-analysis-commands)
  - [Cache Management Commands](#cache-management-commands)
- [Implementation Status](#implementation-status)
  - [Language Pack Integration](#language-pack-integration)
  - [Implementation Gaps](#implementation-gaps)
  - [MCP SDK Implementation](#mcp-sdk-implementation)
- [Implementation Notes](#implementation-notes)
- [Testing Guidelines](#testing-guidelines)
- [Implementation Progress](#implementation-progress)

---

## Supported Languages

The following programming languages are fully supported with symbol extraction, AST analysis, and query capabilities:

| Language | Symbol Extraction | AST Analysis | Query Support |
|----------|-------------------|--------------|--------------|  
| Python | ✅ | ✅ | ✅ |
| JavaScript | ✅ | ✅ | ✅ |
| TypeScript | ✅ | ✅ | ✅ |
| Go | ✅ | ✅ | ✅ |
| Rust | ✅ | ✅ | ✅ |
| C | ✅ | ✅ | ✅ |
| C++ | ✅ | ✅ | ✅ |
| Swift | ✅ | ✅ | ✅ |
| Java | ✅ | ✅ | ✅ |
| Kotlin | ✅ | ✅ | ✅ |
| Julia | ✅ | ✅ | ✅ |
| APL | ✅ | ✅ | ✅ |

Additional languages are available via tree-sitter-language-pack, including Bash, C#, Clojure, Elixir, Elm, Haskell, Lua, Objective-C, OCaml, PHP, Protobuf, Ruby, Scala, SCSS, SQL, and XML.

---

## Command Status Legend

| Status | Meaning |
|--------|---------|
| ✅ | Working - Feature is fully operational |
| ⚠️ | Partially Working - Feature works with limitations or in specific conditions |
| ❌ | Not Working - Feature fails or is unavailable |
| 🔄 | Requires Dependency - Needs external components (e.g., language parsers) |

---

## Command Reference

### Project Management Commands

These commands handle project registration and management.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `register_project_tool` | ✅ | None | Successfully registers projects with path, name, and description |
| `list_projects_tool` | ✅ | None | Successfully lists all registered projects |
| `remove_project_tool` | ✅ | None | Successfully removes registered projects |

**Example Usage:**
```python
# Register a project
register_project_tool(path="/path/to/project", name="my-project", description="My awesome project")

# List all projects
list_projects_tool()

# Remove a project
remove_project_tool(name="my-project")
```

### Language Tools Commands

These commands manage tree-sitter language parsers.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `list_languages` | ✅ | None | Lists all available languages from tree-sitter-language-pack |
| `check_language_available` | ✅ | None | Checks if a specific language is available via tree-sitter-language-pack |

**Example Usage:**
```python
# List all available languages
list_languages()

# Check if a specific language is available
check_language_available(language="python")
```

### File Operations Commands

These commands access and manipulate project files.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `list_files` | ✅ | Project registration | Successfully lists files with optional filtering |
| `get_file` | ✅ | Project registration | Successfully retrieves file content |
| `get_file_metadata` | ✅ | Project registration | Returns file information including size, modification time, etc. |

**Example Usage:**
```python
# List Python files
list_files(project="my-project", pattern="**/*.py")

# Get file content
get_file(project="my-project", path="src/main.py")

# Get file metadata
get_file_metadata(project="my-project", path="src/main.py")
```

### AST Analysis Commands

These commands perform abstract syntax tree (AST) operations.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `get_ast` | ✅ | Project registration | Returns AST using efficient cursor-based traversal with proper node IDs |
| `get_node_at_position` | ✅ | Project registration | Successfully retrieves nodes at a specific position in a file |

**Example Usage:**
```python
# Get AST for a file
get_ast(project="my-project", path="src/main.py", max_depth=5, include_text=True)

# Find node at position
get_node_at_position(project="my-project", path="src/main.py", row=10, column=5)
```

### Search and Query Commands

These commands search code and execute tree-sitter queries.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `find_text` | ✅ | Project registration | Text search works correctly with pattern matching |
| `run_query` | ✅ | Project registration, Language | Successfully executes tree-sitter queries and returns results |
| `get_query_template_tool` | ✅ | None | Successfully returns templates when available |
| `list_query_templates_tool` | ✅ | None | Successfully lists available templates |
| `build_query` | ✅ | None | Successfully builds and combines query templates |
| `adapt_query` | ✅ | None | Successfully adapts queries between different languages |
| `get_node_types` | ✅ | None | Successfully returns descriptions of node types for a language |

**Example Usage:**
```python
# Find text in project files
find_text(project="my-project", pattern="TODO", file_pattern="**/*.py")

# Run a tree-sitter query
run_query(
    project="my-project",
    query="(function_definition name: (identifier) @function.name) @function.def",
    file_path="src/main.py",
    language="python"
)

# List query templates for a language
list_query_templates_tool(language="python")

# Get descriptions of node types
get_node_types(language="python")
```

### Code Analysis Commands

These commands analyze code structure and complexity.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `get_symbols` | ✅ | Project registration | Successfully extracts symbols (functions, classes, imports) from files |
| `analyze_project` | ✅ | Project registration | Project structure analysis works with support for detailed code analysis |
| `get_dependencies` | ✅ | Project registration | Successfully identifies dependencies from import statements |
| `analyze_complexity` | ✅ | Project registration | Provides accurate code complexity metrics |
| `find_similar_code` | ⚠️ | Project registration | Execution successful but no results returned in testing |
| `find_usage` | ✅ | Project registration | Successfully finds usage of symbols across project files |

**Example Usage:**
```python
# Extract symbols from a file
get_symbols(project="my-project", file_path="src/main.py")

# Analyze project structure
analyze_project(project="my-project", scan_depth=3)

# Get dependencies for a file
get_dependencies(project="my-project", file_path="src/main.py")

# Analyze code complexity
analyze_complexity(project="my-project", file_path="src/main.py")

# Find similar code
find_similar_code(
    project="my-project",
    snippet="print('Hello, world!')",
    language="python"
)

# Find symbol usage
find_usage(project="my-project", symbol="main", language="python")
```

### Configuration Management Commands

These commands manage the service and its parse tree cache.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `clear_cache` | ✅ | None | Successfully clears caches at all levels (global, project, or file) |
| `configure` | ✅ | None | Successfully configures cache, log level, and other settings |
| `diagnose_config` | ✅ | None | Diagnoses issues with YAML configuration loading |

**Example Usage:**
```python
# Clear all caches
clear_cache()

# Clear cache for a specific project
clear_cache(project="my-project")

# Configure cache settings
configure(cache_enabled=True, max_file_size_mb=10, log_level="DEBUG")

# Diagnose configuration issues
diagnose_config(config_path="/path/to/config.yaml")
```

---

## Implementation Status

### Language Pack Integration

The integration of tree-sitter-language-pack is complete with comprehensive language support. All 31 languages are available and functional.

| Feature Area | Status | Test Results |
|--------------|--------|--------------|
| Language Tools | ✅ Working | All tests pass. Language tools properly report and list available languages |
| AST Analysis | ✅ Working | All tests pass. `get_ast` and `get_node_at_position` work correctly with proper node IDs and AST traversal operations |
| Search Queries | ✅ Working | All tests pass. Text search works, query building works, and tree-sitter query execution returns expected results |
| Code Analysis | ✅ Working | All tests pass. Structure and complexity analysis works, symbol extraction and dependency analysis provide useful results |

**Current Integration Capabilities:**
- AST functionality works well for retrieving and traversing trees and nodes
- Query execution and result handling work correctly
- Symbol extraction and dependency analysis provide useful results
- Project management, file operations, and search features work correctly

### Implementation Gaps

Based on the latest tests as of March 18, 2025, these are the current implementation gaps:

#### Tree Editing and Incremental Parsing
- **Status:** ⚠️ Partially Working
- Core AST functionality works
- Tree manipulation functionality requires additional implementation

#### Tree Cursor API
- **Status:** ✅ Fully Working
- AST node traversal works correctly
- Cursor-based tree walking is efficient and reliable
- Can be extended for more advanced semantic analysis

#### Similar Code Detection
- **Status:** ⚠️ Partially Working
- Command executes successfully but testing did not yield results
- May require more specific snippets or fine-tuning of similarity thresholds

#### UTF-16 Support
- **Status:** ❌ Not Implemented
- Encoding detection and support is not yet available
- Will require parser improvements after core AST functionality is fixed

#### Read Callable Support
- **Status:** ❌ Not Implemented
- Custom read strategies are not yet available
- Streaming parsing for large files remains unavailable

### MCP SDK Implementation

| Feature | Status | Notes |
|---------|--------|-------|
| Application Lifecycle Management | ✅ Working | Basic lifespan support is functioning correctly |
| Image Handling | ❌ Not Implemented | No support for returning images from tools |
| MCP Context Handling | ⚠️ Partial | Basic context access works, but progress reporting not fully implemented |
| Claude Desktop Integration | ✅ Working | MCP server can be installed in Claude Desktop |
| Server Capabilities Declaration | ✅ Working | Capabilities are properly declared |

---

## Implementation Notes

This project uses a structured dependency injection (DI) pattern, but still has global singletons at its core:

1. A central `DependencyContainer` singleton that holds all shared services
2. A `global_context` object that provides a convenient interface to the container
3. API functions that access the container internally

This architecture provides three main ways to access functionality:

```python
# Option 1: API Functions (preferred for most use cases)
from mcp_server_tree_sitter.api import get_config, get_language_registry

config = get_config()
languages = get_language_registry().list_available_languages()

# Option 2: Direct Container Access
from mcp_server_tree_sitter.di import get_container

container = get_container()
project_registry = container.project_registry
tree_cache = container.tree_cache

# Option 3: Global Context
from mcp_server_tree_sitter.context import global_context

config = global_context.get_config()
result = global_context.register_project("/path/to/project")
```

The dependency injection approach helps make the code more testable and maintainable, even though it still uses singletons internally.

---

## Testing Guidelines

When testing the MCP Tree-sitter server, use this structured approach:

1. **Project Setup**
   - Register a project with `register_project_tool`
   - Verify registration with `list_projects_tool`

2. **Basic File Operations**
   - Test `list_files` to ensure project access
   - Test `get_file` to verify content retrieval
   - Test `get_file_metadata` to check file information

3. **Language Parser Verification**
   - Test `check_language_available` to verify specific language support
   - Use `list_languages` to see all available languages

4. **Feature Testing**
   - Test AST operations with `get_ast` to ensure proper node IDs and structure
   - Test query execution with `run_query` to verify proper result capture
   - Test symbol extraction with `get_symbols` to verify proper function, class, and import detection
   - Test dependency analysis with `get_dependencies` to verify proper import detection
   - Test complexity analysis with `analyze_complexity` to verify metrics are being calculated correctly
   - Test usage finding with `find_usage` to verify proper symbol reference detection

5. **Test Outcomes**
   - All 185 tests now pass successfully
   - No diagnostic errors reported
   - Core functionality works reliably across all test cases

---

## Implementation Progress

Based on the test results as of March 18, 2025, all critical functionality is now working:

1. **✅ Tree-Sitter Query Result Handling**
   - Query result handling works correctly
   - Queries execute and return proper results with correct capture processing

2. **✅ Tree Cursor Functionality**
   - Tree cursor-based traversal is working correctly
   - Efficient navigation and analysis of ASTs is now possible

3. **✅ AST Node ID Generation**
   - AST nodes are correctly assigned unique IDs
   - Node traversal and reference works reliably

4. **✅ Symbol Extraction**
   - Symbol extraction correctly identifies functions, classes, and imports
   - Location information is accurate

5. **✅ Dependency Analysis**
   - Dependency analysis correctly identifies imports and references
   - Properly handles different import styles

6. **✅ Code Complexity Analysis**
   - Complexity metrics are calculated correctly
   - Line counts, cyclomatic complexity, and other metrics are accurate

7. **⚠️ Similar Code Detection**
   - Command completes execution but testing did not yield results
   - May need further investigation with more appropriate test cases

8. **Future Work: Complete MCP Context Progress Reporting**
   - Add progress reporting for long-running operations to improve user experience

---

This feature matrix reflects test results as of March 18, 2025. All core functionality is now working correctly, with only minor issues in similar code detection. The project is fully operational with all 185 tests passing successfully.
