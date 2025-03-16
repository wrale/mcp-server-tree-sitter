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
| `list_languages` | ⚠️ | None | Currently returns empty available/installable languages list |
| `install_language` | ✅ | None | Successfully reports language availability via tree-sitter-language-pack |

### Common Failure Modes:
- `list_languages` returns empty lists despite languages being available
- Language availability check through `install_language` works, but languages don't appear in lists

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
| `get_ast` | ❌ | None | Currently fails with error code 4384162096 |
| `get_node_at_position` | ❌ | None | Not tested but likely fails due to AST parsing issues |

### Common Failure Modes:
- `get_ast` fails with error code rather than informative error message
- AST parsing functionality appears to be non-operational

## Search and Query Commands

These commands search code and execute tree-sitter queries.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `find_text` | ✅ | Project registration | Text search works without language parsers |
| `run_query` | ❌ | None | Not tested but likely fails due to AST parsing issues |
| `get_query_template_tool` | ✅ | None | Successfully returns query templates for language |
| `list_query_templates_tool` | ✅ | None | Successfully lists available query templates |
| `build_query` | ❌ | None | Not tested but likely fails with complex queries |
| `adapt_query` | ❌ | None | Not tested but likely fails with current implementation |
| `get_node_types` | ✅ | None | Successfully returns node type descriptions |

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
| `get_symbols` | ❌ | None | Fails with "too many values to unpack (expected 2)" |
| `analyze_project` | ✅ | Project registration | Project structure analysis works, but detailed analysis fails |
| `get_dependencies` | ❌ | None | Fails with "too many values to unpack (expected 2)" |
| `analyze_complexity` | ❌ | None | Fails with "too many values to unpack (expected 2)" |
| `find_similar_code` | ❌ | None | Not tested but likely fails in current implementation |
| `find_usage` | ❌ | None | Not tested but likely fails in current implementation |

### Common Failure Modes:
- Several commands fail with "too many values to unpack (expected 2)" error
- Core functionality dependent on AST parsing fails with current implementation

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
| Language Tools | ⚠️ Partial | ⚠️ Partial | Language detection works but listing fails |
| AST Analysis | ⚠️ Partial | ❌ Not Working | Core AST functionality fails with errors |
| Search Queries | ⚠️ Partial | ⚠️ Partial | Text search works but AST queries fail |
| Code Analysis | ⚠️ Partial | ❌ Not Working | Analysis functions fail with errors |

### Current Integration Issues:
- Basic language detection works through `install_language` command
- AST parsing appears to be broken, affecting multiple dependent commands
- Several commands that rely on AST functionality fail with unpacking errors
- Project management and file operations continue to function properly

## Testing Guidelines

When testing the MCP Tree-sitter server, use this structured approach:

1. **Project Setup**:
   - Register a project with `register_project_tool`
   - Verify registration with `list_projects_tool`

2. **Basic File Operations**:
   - Test `list_files` to ensure project access
   - Test `get_file` to verify content retrieval

3. **Language Parser Verification**:
   - Test `install_language` to check language availability
   - Note that `list_languages` currently returns empty results

4. **Feature Testing**:
   - Focus on working features: project management, file operations, text search
   - Document errors in AST and analysis operations for debugging

5. **Error Cases**:
   - Common error: "too many values to unpack (expected 2)"
   - AST operations failing with numeric error codes

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| AST parsing failures | Implementation issues with tree-sitter integration | Needs code fixes in AST handling |
| "too many values to unpack (expected 2)" | Likely tuple unpacking error in query code | Needs code fix in capture handling |
| Empty language lists | Issues with language registry | Check language registry implementation |
| Numeric error codes | Exception handling not properly configured | Enhance error reporting |

---

This feature matrix reflects test results as of March 16, 2025. Several critical functions need implementation fixes to become operational.
