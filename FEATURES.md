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
| `list_languages` | ✅ | None | Returns available and installable languages |
| `install_language` | ❌/🔄 | Language parsers or tree-sitter-language-pack | Without tree-sitter-language-pack, fails with "Automatic installation disabled" |

### Common Failure Modes:
- Language installation fails when auto-install is disabled (default)
- Languages may be unavailable even when requested to install
- Requires server restart after language installation

### After tree-sitter-language-pack Implementation:
Once tree-sitter-language-pack is implemented, both commands should work without dependencies or installation requirements.

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
| `get_ast` | 🔄 | Language parser for file type | Requires correct language parser to be installed |
| `get_node_at_position` | 🔄 | Language parser for file type | Requires correct language parser to be installed |

### Common Failure Modes:
- Fails with "Language not available" when appropriate parser isn't installed
- May fail with encoding errors on non-UTF8 files

### After tree-sitter-language-pack Implementation:
These commands should work for all supported languages without additional installations.

## Search and Query Commands

These commands search code and execute tree-sitter queries.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `find_text` | ✅ | Project registration | Text search works without language parsers |
| `run_query` | 🔄 | Language parser for file type | Requires language parser to be installed |
| `get_query_template_tool` | 🔄 | Language parser for file type | Requires language parser to be installed |
| `list_query_templates_tool` | ✅ | None | Works even without language parsers |
| `build_query` | 🔄 | Language parser for specific language | Requires language parser to be installed |
| `adapt_query` | 🔄 | Language parsers for both languages | Requires language parsers to be installed |
| `get_node_types` | 🔄 | Language parser for specific language | Requires language parser to be installed |

### Example Usage:
```python
# Find text in project files
find_text(project="my-project", pattern="TODO", file_pattern="**/*.py")

# Run a tree-sitter query
run_query(
    project="my-project",
    query='(function_definition name: (identifier) @function.name)',
    language="python"
)
```

## Code Analysis Commands

These commands analyze code structure and complexity.

| Command | Status | Dependencies | Notes |
|---------|--------|--------------|-------|
| `get_symbols` | 🔄 | Language parser for file type | Fails with "Language not available" when parser isn't installed |
| `analyze_project` | ✅ | Project registration | Structure analysis works without language parsers |
| `get_dependencies` | 🔄 | Language parser for file type | Requires language parser to be installed |
| `analyze_complexity` | 🔄 | Language parser for file type | Requires language parser to be installed |
| `find_similar_code` | 🔄 | Language parser for file type | Requires language parser to be installed |
| `find_usage` | 🔄 | Language parser for file type | Requires language parser to be installed |

### Common Failure Modes:
- Symbol extraction fails when language parser is not installed
- Language-specific analysis fails without the correct parser

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

The integration of tree-sitter-language-pack will solve most dependency issues by providing all necessary language parsers in a single package.

| Feature Area | Current Status | After Integration |
|--------------|----------------|-------------------|
| Language Tools | ⚠️ Partial | ✅ Full Support |
| AST Analysis | ⚠️ Partial | ✅ Full Support |
| Search Queries | ⚠️ Partial | ✅ Full Support |
| Code Analysis | ⚠️ Partial | ✅ Full Support |

### Benefits of Integration:
- All commands will work without requiring individual language installations
- No server restarts needed when accessing new languages
- Consistent behavior across different language types
- Access to 100+ tree-sitter grammars in a single dependency

## Testing Guidelines

When testing the MCP Tree-sitter server, use this structured approach:

1. **Project Setup**:
   - Register a project with `register_project_tool`
   - Verify registration with `list_projects_tool`

2. **Basic File Operations**:
   - Test `list_files` to ensure project access
   - Test `get_file` to verify content retrieval

3. **Language Parser Verification**:
   - Test `list_languages` to check available languages
   - If using language-specific features, check parser availability

4. **Feature Testing**:
   - Test general features first (text search, project analysis)
   - Test language-specific features with available parsers
   - Document any failures with specific error messages

5. **Error Cases**:
   - Test behavior with invalid inputs
   - Verify appropriate error messages
   - Check recovery after errors

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Language not available" | Missing language parser | Install tree-sitter-language-pack |
| "Automatic installation disabled" | Default config setting | Enable auto_install or use language pack |
| "Project not found" | Missing project registration | Register project before other operations |
| "Access denied" | Path outside project root | Use paths within project directory |
| "File too large" | File exceeds size limit | Increase max_file_size_mb in config |

---

This feature matrix will be updated as development progresses and as the tree-sitter-language-pack integration is completed.
