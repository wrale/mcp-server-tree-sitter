# MCP Tree-sitter Server — API Reference

**Temporary file.** Stored in `results/` (gitignored). Describes all MCP **tools** (arguments, description, return shape). Prompts are listed at the end without full detail.

---

## Configuration

### `configure`

Configure the server (YAML load and/or overrides).

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `config_path` | `str` | No | Path to YAML config file |
| `cache_enabled` | `bool` | No | Enable/disable parse tree caching |
| `max_file_size_mb` | `int` | No | Max file size to process (MB) |
| `log_level` | `str` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

**Returns:** `Dict` — Current configuration (same shape as below).

```json
{
  "cache": { "enabled": true, "max_size_mb": 100, "ttl_seconds": 300 },
  "security": { "max_file_size_mb": 5, "excluded_dirs": [".git", "node_modules", ...] },
  "language": { "auto_install": false, "default_max_depth": 5 },
  "log_level": "INFO"
}
```

---

## Project management

### `register_project_tool`

Register a project directory for analysis.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `path` | `str` | Yes | Absolute or relative path to project root |
| `name` | `str` | No | Project name (default: last path component) |
| `description` | `str` | No | Optional description |

**Returns:** `Dict` — Registered project info.

```json
{
  "name": "my-project",
  "root_path": "/abs/path/to/project",
  "description": null,
  "languages": { "python": 42, "javascript": 10 },
  "last_scan_time": 1234567890
}
```

### `list_projects_tool`

List all registered projects.

**Arguments:** None.

**Returns:** `List[Dict]` — Same shape as one project in `register_project_tool`.

### `remove_project_tool`

Remove a registered project.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `str` | Yes | Project name |

**Returns:** `Dict` — `{ "status": "success", "message": "Project 'name' removed" }`.

---

## Language

### `list_languages`

List available tree-sitter languages.

**Arguments:** None.

**Returns:** `Dict` — `{ "available": ["python", "javascript", ...], "installable": [] }`.

### `check_language_available`

Check if a language parser is available.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `language` | `str` | Yes | Language id (e.g. `python`, `javascript`) |

**Returns:** `Dict` — Success: `{ "status": "success", "message": "Language 'x' is available via ..." }`. Error: `{ "status": "error", "message": "Language 'x' is not available" }`.

---

## File operations

### `list_files`

List files in a project.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `pattern` | `str` | No | Glob (e.g. `**/*.py`). Default `**/*` |
| `max_depth` | `int` | No | Max directory depth for glob |
| `extensions` | `List[str]` | No | Include only these extensions (no dot) |

**Returns:** `List[str]` — Relative file paths.

### `get_file`

Get file content.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `path` | `str` | Yes | Path relative to project root |
| `max_lines` | `int` | No | Cap number of lines returned |
| `start_line` | `int` | No | First line (0-based). Default 0 |

**Returns:** `str` — File content (or slice).

### `get_file_metadata`

Get file metadata.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `path` | `str` | Yes | Path relative to project root |

**Returns:** `Dict` —

```json
{
  "path": "src/main.py",
  "size": 1024,
  "last_modified": 1234567890.0,
  "created": 1234567890.0,
  "is_directory": false,
  "extension": "py",
  "line_count": 50
}
```

---

## AST

### `get_ast`

Get abstract syntax tree for a file.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `path` | `str` | Yes | Path relative to project root |
| `max_depth` | `int` | No | Max tree depth (default from config, typically 5) |
| `include_text` | `bool` | No | Include node text. Default true |

**Returns:** `Dict` —

```json
{
  "file": "src/main.py",
  "language": "python",
  "tree": {
    "id": 12345,
    "type": "module",
    "start_point": { "row": 0, "column": 0 },
    "end_point": { "row": 10, "column": 0 },
    "start_byte": 0,
    "end_byte": 500,
    "named": true,
    "children_count": 5,
    "text": "...",
    "children": [ { "id": ..., "type": "...", ... } ]
  }
}
```

Each node can have: `id`, `type`, `start_point`, `end_point`, `start_byte`, `end_byte`, `named`, `children_count`, optional `text`, optional `children` (same shape, up to `max_depth`).

### `get_node_at_position`

Get the AST node at a given position.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `path` | `str` | Yes | Path relative to project root |
| `row` | `int` | Yes | Line (0-based) |
| `column` | `int` | Yes | Column (0-based) |

**Returns:** `Dict` or `null` — Same node shape as in `get_ast` (limited depth), or `null` if no node.

### `get_enclosing_scope`

Find the enclosing scope (function, class, or module) for a given position. All line/column values are 0-based.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `file_path` | `str` | Yes | Path relative to project root |
| `row` | `int` | Yes | Line (0-based) |
| `column` | `int` | Yes | Column (0-based) |
| `label` | `str` | No | Optional text label at the position (e.g. variable name) |

**Returns:** `Dict` — Enclosing scope info, or empty dict if no scope (e.g. position outside valid code).

```json
{
  "kind": "function",
  "text": "def foo():\n    return 1",
  "start_line": 0,
  "end_line": 1
}
```

- `kind`: One of `function`, `class`, `module` (or language-specific equivalent).
- `text`: Source text of the scope node.
- `start_line`, `end_line`: 0-based inclusive line range of the scope.

---

## Search and queries

### `find_text`

Text search in project files.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `pattern` | `str` | Yes | Search string (or regex if `use_regex`) |
| `file_pattern` | `str` | No | Glob to restrict files (e.g. `**/*.py`) |
| `max_results` | `int` | No | Max matches. Default 100 |
| `case_sensitive` | `bool` | No | Default false |
| `whole_word` | `bool` | No | Default false |
| `use_regex` | `bool` | No | Default false |
| `context_lines` | `int` | No | Lines before/after. Default 2 |

**Returns:** `List[Dict]` —

```json
[
  {
    "file": "src/main.py",
    "line": 10,
    "text": "  def foo():",
    "context": [
      { "line": 9, "text": "...", "is_match": false },
      { "line": 10, "text": "  def foo():", "is_match": true },
      { "line": 11, "text": "...", "is_match": false }
    ]
  }
]
```

### `run_query`

Run a tree-sitter query on project files.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `query` | `str` | Yes | Tree-sitter query string |
| `file_path` | `str` | No | Single file; if omitted, all files for `language` |
| `language` | `str` | No | Required if `file_path` not set (e.g. `python`) |
| `max_results` | `int` | No | Default 100 |

**Returns:** `List[Dict]` —

```json
[
  {
    "file": "src/main.py",
    "capture": "function.name",
    "start": { "row": 0, "column": 4 },
    "end": { "row": 0, "column": 7 },
    "text": "foo"
  }
]
```

### `get_query_template_tool`

Get a predefined query template.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `language` | `str` | Yes | e.g. `python`, `javascript` |
| `template_name` | `str` | Yes | e.g. `functions`, `classes`, `imports` |

**Returns:** `Dict` — `{ "language": "python", "name": "functions", "query": "(function_definition ...) @func" }`. Raises if template missing.

### `list_query_templates_tool`

List query templates.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `language` | `str` | No | If set, only that language’s templates |

**Returns:** `Dict` — `{ "python": { "functions": "...", "classes": "..." }, ... }` or single language.

### `build_query`

Build a compound query from template names or patterns.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `language` | `str` | Yes | Language id |
| `patterns` | `List[str]` | Yes | Template names or raw patterns |
| `combine` | `str` | No | `"or"` or `"and"`. Default `"or"` |

**Returns:** `Dict` — `{ "language": "python", "query": "..." }`.

### `adapt_query`

Adapt a query from one language to another (node-type mapping).

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `query` | `str` | Yes | Original query |
| `from_language` | `str` | Yes | Source language |
| `to_language` | `str` | Yes | Target language |

**Returns:** `Dict` — `{ "original_language": "python", "target_language": "javascript", "original_query": "...", "adapted_query": "..." }`.

### `get_node_types`

Get short descriptions of common node types for a language.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `language` | `str` | Yes | Language id |

**Returns:** `Dict[str, str]` — `{ "function_definition": "A function definition with name and params", ... }`.

---

## Analysis

### `get_symbols`

Extract symbols (functions, classes, imports, etc.) from a file.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `file_path` | `str` | Yes | Path relative to project root |
| `symbol_types` | `List[str]` | No | e.g. `["functions", "classes", "imports"]`; language-specific defaults if omitted |

**Returns:** `Dict[str, List[Dict]]` — One key per symbol type, value list of symbols:

```json
{
  "functions": [
    {
      "name": "main",
      "type": "functions",
      "location": {
        "start": { "row": 0, "column": 4 },
        "end": { "row": 2, "column": 10 }
      }
    }
  ],
  "classes": [...],
  "imports": [...]
}
```

### `analyze_project`

Analyze project structure (languages, entry points, build files, dir/file counts, sample symbol counts).

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `scan_depth` | `int` | No | Depth for sampling files. Default 3 |
| `ctx` | any | No | Optional MCP context for progress |

**Returns:** `Dict` —

```json
{
  "name": "my-project",
  "path": "/abs/path",
  "languages": { "python": 42, "javascript": 10 },
  "entry_points": [ { "path": "src/main.py", "language": "python" } ],
  "build_files": [ { "path": "pyproject.toml", "type": "python" } ],
  "dir_counts": { "": 5, "src": 2 },
  "file_counts": { ".py": 42, ".js": 10 },
  "total_files": 52,
  "key_files_analysis": {
    "python": [ { "file": "src/a.py", "symbols": { "functions": 3, "classes": 1 } } ]
  }
}
```

### `get_dependencies`

Find imports/dependencies of a file.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `file_path` | `str` | Yes | Path relative to project root |

**Returns:** `Dict[str, List[str]]` — Categories (e.g. `module`, `from`, `item`, `alias`) to list of names:

```json
{
  "module": ["os", "sys"],
  "from": ["pathlib"],
  "item": ["Path"]
}
```

### `analyze_complexity`

Code complexity and size metrics for a file.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `file_path` | `str` | Yes | Path relative to project root |

**Returns:** `Dict` —

```json
{
  "line_count": 100,
  "code_lines": 80,
  "empty_lines": 10,
  "comment_lines": 10,
  "comment_ratio": 0.1,
  "function_count": 5,
  "class_count": 2,
  "avg_function_lines": 12.5,
  "cyclomatic_complexity": 8,
  "language": "python"
}
```

### `find_similar_code`

Find code similar to a snippet (currently implemented as text search).

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `snippet` | `str` | Yes | Code snippet to match |
| `language` | `str` | No | Restricts to that language’s extensions |
| `threshold` | `float` | No | Similarity (0–1). Default 0.8 (not used by current impl) |
| `max_results` | `int` | No | Default 10 |

**Returns:** Same structure as `find_text` (list of matches with `file`, `line`, `text`, `context`).

### `find_usage`

Find usages of a symbol (identifier) in the project.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | Yes | Project name |
| `symbol` | `str` | Yes | Symbol name |
| `file_path` | `str` | No | Limit to one file (language inferred) |
| `language` | `str` | No | Required if `file_path` not set |

**Returns:** Same structure as `run_query`: list of `{ "file", "capture", "start", "end", "text" }`.

---

## Cache and debug

### `clear_cache`

Clear parse tree cache.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | `str` | No | If set with `file_path`, clear only that file |
| `file_path` | `str` | No | With `project`: clear one file; with only `project`: clear project; neither: clear all |

**Returns:** `Dict` — `{ "status": "success", "message": "..." }`.

### `diagnose_config`

Diagnose YAML config loading.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `config_path` | `str` | Yes | Path to YAML file |

**Returns:** `Dict` —

```json
{
  "file_path": "/path/to/config.yaml",
  "exists": true,
  "readable": true,
  "yaml_valid": true,
  "parsed_data": { ... },
  "file_content": "...",
  "config_before": { "cache.max_size_mb": 100, ... },
  "config_after": { ... },
  "new_config": { ... },
  "error": null
}
```

On error, `error` is set and some other fields may be null.

---

## Prompts (summary)

These are MCP **prompts** (templates returning a string for the LLM), not tools:

| Name | Arguments | Purpose |
|------|-----------|--------|
| `code_review` | `project`, `file_path` | Prompt to review a file (with symbols summary) |
| `explain_code` | `project`, `file_path`, `focus` (optional) | Prompt to explain the file |
| `explain_tree_sitter_query` | — | Explains tree-sitter query syntax and asks for a query |
| `suggest_improvements` | `project`, `file_path` | Prompt to suggest improvements (includes complexity metrics) |
| `project_overview` | `project` | Prompt to analyze project (uses `analyze_project` data) |

---

*Generated from the codebase. For authoritative behavior, see `src/mcp_server_tree_sitter/tools/registration.py` and the tool implementations.*
