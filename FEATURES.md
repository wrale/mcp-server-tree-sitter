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
| `list_languages` | ❌ | None | Returns empty available/installable languages lists despite languages being available |
| `install_language` | ✅ | None | Successfully reports language availability via tree-sitter-language-pack |

### Common Failure Modes:
- `list_languages` returns empty lists despite languages being available through `install_language`
- Language registry implementation doesn't correctly populate available languages

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
| `get_query_template_tool` | ⚠️ | None | Not fully tested but likely returns templates when available |
| `list_query_templates_tool` | ⚠️ | None | Not fully tested but likely lists available templates |
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
| `find_similar_code` | ❌ | None | Not fully tested but likely limited to text-based matching |
| `find_usage` | ❌ | None | Not fully tested but likely fails due to AST parsing issues |

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
configure(cache_enabled=True, max_file_size_mb=10, log_level="DEBUG")
```

## Tree-sitter Language Pack Integration Status

The integration of tree-sitter-language-pack appears to be partially complete, but core functionality issues remain.

| Feature Area | Previous Status | Current Status | Test Results |
|--------------|-----------------|----------------|--------------|
| Language Tools | ⚠️ Partial | ⚠️ Partial | `install_language` reports languages as available, but `list_languages` returns empty lists |
| AST Analysis | ⚠️ Partial | ❌ Not Working | `get_ast` fails with node ID errors, showing issues with AST building |
| Search Queries | ⚠️ Partial | ⚠️ Partial | Text search works but tree-sitter queries run without returning results |
| Code Analysis | ⚠️ Partial | ⚠️ Partial | Basic structure analysis works, but symbol extraction and AST-dependent features return empty results |

### Current Integration Issues:
- Discrepancy between language detection and language listing
- AST parsing returns errors about missing node IDs
- Query execution completes but doesn't return proper results
- Analysis functions run but return empty or limited results
- Project management and file operations function correctly

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
   - Test `install_language` to check language availability
   - Note that `list_languages` currently returns empty results

4. **Feature Testing**:
   - Focus on working features: project management, file operations, text search, basic project analysis
   - Document empty results from AST-dependent operations for debugging

5. **Error Cases**:
   - AST operations returning errors about missing node IDs
   - Empty results from symbol extraction and dependency analysis
   - Query execution without result output

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty language lists | Discrepancy between language detection and listing | Fix language registry implementation |
| AST parsing node ID errors | Issues with tree-sitter integration | Fix AST node dictionary building in models/ast.py |
| Empty results from analysis | Problems with AST traversal | Update cursor-based traversal to handle errors gracefully |
| Query execution without output | Issues with query capture handling | Fix capture handling in query_code function |

---

This feature matrix reflects test results as of March 16, 2025. While basic functionality works, AST-dependent features need implementation fixes to become fully operational.
