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
| `get_ast` | ✅ | None | Returns AST using efficient cursor-based traversal |
| `get_node_at_position` | ✅ | None | Successfully retrieves nodes at a specific position in a file |

**Previous Issues (Now Fixed):**
- ✅ `get_ast` now returns proper AST with node IDs
- ✅ AST parsing functionality is fully operational with tree-sitter-language-pack integration

### Search and Query Commands

These commands search code and execute tree-sitter queries.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `find_text` | ✅ | Project registration | Text search works correctly with pattern matching |
| `run_query` | ✅ | None | Successfully executes tree-sitter queries and returns results |
| `get_query_template_tool` | ✅ | None | Successfully returns templates when available |
| `list_query_templates_tool` | ✅ | None | Successfully lists available templates |
| `build_query` | ✅ | None | Successfully builds and combines query templates |
| `adapt_query` | ✅ | None | Successfully adapts queries between different languages |
| `get_node_types` | ✅ | None | Successfully returns descriptions of node types for a language |

**Example Usage:**
```python
# Find text in project files
find_text(project="my-project", pattern="TODO", file_pattern="**/*.py")

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
| `find_similar_code` | ✅ | None | Finds similar code patterns across project files |
| `find_usage` | ✅ | None | Successfully finds usage of symbols across project files |

**Previous Issues (Now Fixed):**
- ✅ Commands now return proper results rather than empty data
- ✅ AST-dependent functionality now works reliably with all supported languages

### Cache Management Commands

These commands manage the parse tree cache.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `clear_cache` | ✅ | None | Successfully clears caches at all levels |
| `configure` | ✅ | None | Successfully configures cache, log level, and other settings |

**Example Usage:**
```python
# Clear all caches
clear_cache()

# Clear cache for a specific project
clear_cache(project="my-project")

# Configure cache settings
configure(cache_enabled=True, max_file_size_mb=10, log_level="DEBUG")
```

---

## Implementation Status

### Language Pack Integration

The integration of tree-sitter-language-pack is complete with comprehensive language support.

| Feature Area | Previous Status | Current Status | Test Results |
|--------------|-----------------|----------------|--------------|
| Language Tools | ⚠️ Partial | ✅ Working | Language tools properly report and list available languages |
| AST Analysis | ⚠️ Partial | ✅ Working | `get_ast` and `get_node_at_position` work, and AST traversal operations work correctly |
| Search Queries | ✅ Working | ✅ Working | Text search works, query building works, and tree-sitter query execution returns expected results |
| Code Analysis | ✅ Working | ✅ Working | Structure and complexity analysis works, symbol extraction and dependency analysis provide useful results |

**Current Integration Capabilities:**
- AST functionality works well for retrieving and traversing trees and nodes
- Query execution and result handling work correctly
- Symbol extraction and dependency analysis provide useful results
- Project management, file operations, and search features work correctly

### Implementation Gaps

Based on the latest tests, these are the current implementation gaps:

#### Tree Editing and Incremental Parsing
- **Status:** ⚠️ Partially Working
- Core AST functionality works
- Tree manipulation functionality requires additional implementation

#### Tree Cursor API
- **Status:** ✅ Fully Working
- AST node traversal works correctly
- Cursor-based tree walking is efficient and reliable
- Can be extended for more advanced semantic analysis

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
   - All core features now work as expected: project management, file operations, search, AST operations, query execution
   - All tests pass successfully

5. **Previously Fixed Error Cases**
   - ✅ AST operations previously returned errors about missing node IDs
   - ✅ Symbol extraction and dependency analysis now return expected results
   - ✅ Query execution now returns proper results

---

## Implementation Progress

Based on the test results, these are the recently completed and remaining tasks:

1. **✅ FIXED: Tree-Sitter Query Result Handling**
   - Query result handling has been fixed
   - Queries now execute and return proper results with correct capture processing

2. **✅ FIXED: Tree Cursor Functionality**
   - Tree cursor-based traversal is working correctly
   - Efficient navigation and analysis of ASTs is now possible

3. **✅ FIXED: Query Execution Output**
   - Query execution now returns appropriate results with proper capture handling

4. **Remaining: Complete MCP Context Progress Reporting**
   - Add progress reporting for long-running operations to improve user experience

---

This feature matrix reflects test results as of March 16, 2025. AST functionality, query execution, symbol extraction, and dependency analysis now work correctly. The project is fully operational with all core features working as expected.
