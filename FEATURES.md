# MCP Tree-sitter Server: Feature Matrix

This document provides a comprehensive overview of all MCP Tree-sitter server commands, their status, dependencies, and common usage patterns. It serves as both a reference guide and a test matrix for ongoing development.

## Command Status Legend

| Status | Meaning |
|--------|---------|
| ✅ | Working - Feature is fully operational |
| ⚠️ | Partially Working - Feature works with limitations or in specific conditions |
| ❌ | Not Working - Feature fails or is unavailable |
| 🔄 | Requires Dependency - Needs external components (e.g., language parsers) |

## Project Management Commands

These commands handle project registration and management.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `register_project_tool` | ✅ | None | Successfully registers projects with path, name, and description |
| `list_projects_tool` | ✅ | None | Successfully lists all registered projects |
| `remove_project_tool` | ✅ | None | Successfully removes registered projects |

### Example Usage:
```python
# Register a project
register_project_tool(path="/path/to/project", name="my-project", description="My awesome project")

# List all projects
list_projects_tool()

# Remove a project
remove_project_tool(name="my-project")
```

## Language Tools Commands

These commands manage tree-sitter language parsers.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `list_languages` | ✅ | None | Lists all available languages from tree-sitter-language-pack |
| `check_language_available` | ✅ | None | Checks if a specific language is available via tree-sitter-language-pack |

### Example Usage:
```python
# List all available languages
list_languages()

# Check if a specific language is available
check_language_available(language="python")
```

## File Operations Commands

These commands access and manipulate project files.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `list_files` | ✅ | Project registration | Successfully lists files with optional filtering |
| `get_file` | ✅ | Project registration | Successfully retrieves file content |
| `get_file_metadata` | ✅ | Project registration | Returns file information including size, modification time, etc. |

### Example Usage:
```python
# List Python files
list_files(project="my-project", pattern="**/*.py")

# Get file content
get_file(project="my-project", path="src/main.py")

# Get file metadata
get_file_metadata(project="my-project", path="src/main.py")
```

## AST Analysis Commands

These commands perform abstract syntax tree (AST) operations.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `get_ast` | ❌ | None | Returns error with node ID not found in nodes_dict |
| `get_node_at_position` | ❌ | None | Not fully tested but likely fails due to AST parsing issues |

### Common Failure Modes:
- `get_ast` returns error about missing node IDs rather than a usable AST
- AST parsing functionality appears to be non-operational despite tree-sitter-language-pack integration

## Search and Query Commands

These commands search code and execute tree-sitter queries.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `find_text` | ✅ | Project registration | Text search works correctly with pattern matching |
| `run_query` | ❌ | None | Executes without output but fails to return results |
| `get_query_template_tool` | ✅ | None | Successfully returns templates when available |
| `list_query_templates_tool` | ✅ | None | Successfully lists available templates |
| `build_query` | ❌ | None | Not fully tested but likely fails due to AST parsing issues |
| `adapt_query` | ❌ | None | Not fully tested but likely fails due to AST parsing issues |
| `get_node_types` | ⚠️ | None | Not fully tested but likely works as it doesn't depend on parsing |

### Example Usage:
```python
# Find text in project files
find_text(project="my-project", pattern="TODO", file_pattern="**/*.py")

# List query templates for a language
list_query_templates_tool(language="python")

# Get descriptions of node types
get_node_types(language="python")
```

## Code Analysis Commands

These commands analyze code structure and complexity.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `get_symbols` | ⚠️ | Project registration | Returns empty lists for symbols instead of failing |
| `analyze_project` | ✅ | Project registration | Project structure analysis works, but detailed code analysis is limited |
| `get_dependencies` | ⚠️ | Project registration | Returns empty results instead of failing |
| `analyze_complexity` | ✅ | Project registration | Works but may have limited accuracy due to AST issues |
| `find_similar_code` | ❌ | None | Executes without output but fails to return results |
| `find_usage` | ❌ | None | Executes without output but fails to return results |

### Common Failure Modes:
- Several commands return empty results rather than failing with errors
- AST-dependent functionality is limited despite successful execution

## Cache Management Commands

These commands manage the parse tree cache.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `clear_cache` | ✅ | None | Successfully clears caches at all levels |
| `configure` | ✅ | None | Successfully configures cache, log level, and other settings |

### Example Usage:
```python
# Clear all caches
clear_cache()

# Clear cache for a specific project
clear_cache(project="my-project")

# Configure cache settings
configure(cache_enabled=true, max_file_size_mb=10, log_level="DEBUG")
```

## Tree-sitter Language Pack Integration Status

The integration of tree-sitter-language-pack appears to be partially complete, but core functionality issues remain.

| Feature Area | Previous Status | Current Status | Test Results |
|--------------|-----------------|----------------|--------------|
| Language Tools | ⚠️ Partial | ✅ Working | Language tools properly report and list available languages |
| AST Analysis | ⚠️ Partial | ❌ Not Working | `get_ast` fails with node ID errors, showing issues with AST building |
| Search Queries | ⚠️ Partial | ⚠️ Partial | Text search works but tree-sitter queries run without returning results |
| Code Analysis | ⚠️ Partial | ⚠️ Partial | Basic structure analysis works, but symbol extraction and AST-dependent features return empty results |

### Current Integration Issues:
- AST parsing returns errors about missing node IDs
- Query execution completes but doesn't return proper results
- Analysis functions run but return empty or limited results
- Project management and file operations function correctly

## Implementation Gaps Analysis

Based on the latest tests, these are the current implementation gaps:

### ⚠️ Partial: Tree Editing and Incremental Parsing
- Status: ❌ Not Working
- Core AST functionality must be fixed before these features can be implemented
- Tree manipulation functionality is currently non-operational

### ⚠️ Partial: Tree Cursor API
- Status: ❌ Not Working
- AST node traversal is not functioning correctly
- Core cursor-based tree walking is needed for most advanced functionality

### ❌ Missing: UTF-16 Support
- Status: ❌ Not Implemented
- Encoding detection and support is not yet available
- Will require parser improvements after core AST functionality is fixed

### ❌ Missing: Read Callable Support
- Status: ❌ Not Implemented
- Custom read strategies are not yet available
- Streaming parsing for large files remains unavailable

### MCP SDK Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| Application Lifecycle Management | ✅ Working | Basic lifespan support is functioning correctly |
| Image Handling | ❌ Not Implemented | No support for returning images from tools |
| MCP Context Handling | ⚠️ Partial | Basic context access works, but progress reporting not fully implemented |
| Claude Desktop Integration | ✅ Working | MCP server can be installed in Claude Desktop |
| Server Capabilities Declaration | ✅ Working | Capabilities are properly declared |

## Testing Guidelines

When testing the MCP Tree-sitter server, use this structured approach:

1. **Project Setup**:
   - Register a project with `register_project_tool`
   - Verify registration with `list_projects_tool`

2. **Basic File Operations**:
   - Test `list_files` to ensure project access
   - Test `get_file` to verify content retrieval
   - Test `get_file_metadata` to check file information

3. **Language Parser Verification**:
   - Test `check_language_available` to verify specific language support
   - Use `list_languages` to see all available languages

4. **Feature Testing**:
   - Focus on working features: project management, file operations, text search, basic project analysis
   - Document empty results from AST-dependent operations for debugging

5. **Error Cases**:
   - AST operations returning errors about missing node IDs
   - Empty results from symbol extraction and dependency analysis
   - Query execution without result output

## Critical Next Steps

Based on the testing results, these are the most critical next steps:

1. **Fix AST Node Dictionary Building**: The core issue preventing most functionality appears to be in the AST node dictionary construction. Error "Node ID not found in nodes_dict" indicates a tracking issue during AST creation.

2. **Implement Tree Cursor Functionality**: This is a prerequisite for most advanced features and depends on fixing the core AST handling.

3. **Repair Query Execution Output**: Query execution completes but returns no results, suggesting capture handling issues.

4. **Complete MCP Context Progress Reporting**: Add progress reporting for long-running operations to improve user experience.

---

This feature matrix reflects test results as of March 16, 2025. While basic functionality works, AST-dependent features need implementation fixes to become fully operational.
