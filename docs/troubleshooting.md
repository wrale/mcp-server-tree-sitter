# Troubleshooting Guide

This guide covers common errors, query debugging, performance tuning, environment variables, and how to add a new language.

## Common Errors

### Language and parsing

| Error / symptom | Cause | What to do |
|-----------------|--------|------------|
| **LanguageNotFoundError** | Requested language has no tree-sitter grammar or it failed to load. | Ensure the language is supported (see `language/data/`) and that the tree-sitter language library is installed (e.g. `tree-sitter-python`). Check logs for grammar-load errors. |
| **LanguageInstallError** | Installing a tree-sitter language (e.g. from a grammar repo) failed. | Check network, build tools (e.g. `node`, `npm` for some grammars), and that the grammar repo is compatible with the `tree-sitter` Python binding version. |
| **ParsingError** | Source could not be parsed (syntax error or parser failure). | Verify the file is valid for that language. Try with a minimal file. If the grammar is outdated, consider updating the grammar package. |
| **QueryError** | A tree-sitter query is invalid or fails to run. | See [Query debugging](#query-debugging). Check query syntax and node type names for the grammar. |

### Projects and files

| Error / symptom | Cause | What to do |
|-----------------|--------|------------|
| **ProjectError** (e.g. "Project 'X' already exists") | Duplicate project name or invalid path. | Use a unique name or remove the existing project first. Ensure the path exists and is readable. |
| **FileAccessError** | File or path is not allowed (e.g. outside project, too large, excluded). | Check `security.max_file_size_mb`, `security.excluded_dirs`, and that the path is under a registered project root. |
| **Config file does not exist** | Path passed to configure or `MCP_TS_CONFIG_PATH` points to a missing file. | Create the file or fix the path. Use the debug tool to validate config (see below). |

### Configuration

| Error / symptom | Cause | What to do |
|-----------------|--------|------------|
| YAML parse error when loading config | Invalid YAML or wrong structure. | Validate YAML (syntax and keys). See [config.md](config.md) and [config.example.yaml](config.example.yaml). Use the **diagnose_yaml_config** debug tool if available. |
| Env value not applied / wrong type | Env vars are applied only at load time; type conversion follows existing value. | Set env before starting the server. Use valid values (e.g. numbers for `MCP_TS_CACHE_MAX_SIZE_MB`). See [Environment variable reference](#environment-variable-reference). |

### Cache

| Error / symptom | Cause | What to do |
|-----------------|--------|------------|
| **CacheError** (if raised) | Cache inconsistency or I/O issue. | Clear cache via the clear-cache tool or disable cache temporarily. Check logs. |
| Stale or wrong results after editing files | Cache key uses mtime; sometimes mtime is not updated. | Clear cache for that project/file or disable cache for debugging. |

---

## Query Debugging

Tree-sitter queries are used for symbol extraction, search, and analysis. When a query fails or returns no results:

1. **Check the grammar**  
   Node type names (e.g. `function_definition`, `class_definition`) must match the grammar. Inspect the tree for a small file (e.g. via an AST tool) to see actual node types.

2. **Validate query syntax**  
   Invalid query text causes `tree_sitter.Query()` to raise or produce no matches. Use the tree-sitter query syntax (captures `@name`, predicates, etc.). Comment out parts of the query to find the offending line.

3. **Run with DEBUG logging**  
   Set `MCP_TS_LOG_LEVEL=DEBUG` to see more detail from the server (e.g. which files are parsed, which language is used).

4. **Test on a minimal file**  
   Reproduce with a small snippet that should match. If it matches in isolation but not in a large file, the issue may be scope (e.g. query run on a subtree) or language detection.

5. **Compare with a known-good template**  
   Copy a working query from `language/data/<lang>.py` (e.g. `query_templates`) and adapt gradually.

6. **Debug tools**  
   If the server exposes a tool that runs a custom query or returns the AST for a file, use it to inspect the tree and run small queries.

---

## Performance Tuning

- **Cache**  
  - Enable and size the tree cache for your workload: `cache.enabled`, `cache.max_size_mb`, `cache.ttl_seconds`. Larger cache reduces re-parsing; TTL avoids unbounded growth.  
  - Clear cache when you change config (e.g. security limits) or when you suspect stale trees.

- **Preferred languages**  
  - Set `language.preferred_languages` (config or env) to the languages you use. The server can pre-load these at startup so the first request for that language is faster.

- **File size and exclusions**  
  - Increase `security.max_file_size_mb` only if you need to parse very large files (higher memory and CPU).  
  - Use `security.excluded_dirs` to skip irrelevant directories (e.g. `node_modules`, `.git`, `__pycache__`) and reduce work during project scan and search.

- **Log level**  
  - Use `INFO` or `WARNING` in production; `DEBUG` adds overhead and log volume.

- **Project scope**  
  - Register only the project roots you need; avoid registering huge trees if you only query a subset.

---

## Environment Variable Reference

All configuration-related environment variables use the prefix **`MCP_TS_`**.

**Format:**

- **Section + setting**: `MCP_TS_<SECTION>_<SETTING>` (e.g. `MCP_TS_CACHE_MAX_SIZE_MB`).  
  Section and setting are lowercased and matched to `ServerConfig` (e.g. `cache.max_size_mb`).
- **Top-level setting**: `MCP_TS_<SETTING>` (e.g. `MCP_TS_LOG_LEVEL`).

Values are applied **at config load time only** (startup or when a config file is loaded). Type is inferred from the existing config value (boolean, int, float, or comma-separated list for list fields).

| Variable | Section / key | Type | Default (schema) | Description |
|----------|----------------|------|------------------|--------------|
| `MCP_TS_CONFIG_PATH` | (path to file) | string | — | Path to YAML config file. Used when no explicit path is given. |
| `MCP_TS_LOG_LEVEL` | `log_level` | string | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `MCP_TS_CACHE_ENABLED` | `cache.enabled` | bool | `true` | Enable/disable parse tree cache. |
| `MCP_TS_CACHE_MAX_SIZE_MB` | `cache.max_size_mb` | int | `100` | Max cache size in MB. |
| `MCP_TS_CACHE_TTL_SECONDS` | `cache.ttl_seconds` | int | `300` | Cache entry TTL in seconds. |
| `MCP_TS_SECURITY_MAX_FILE_SIZE_MB` | `security.max_file_size_mb` | int | `5` | Max file size to process (MB). |
| `MCP_TS_SECURITY_EXCLUDED_DIRS` | `security.excluded_dirs` | list | `.git`, `node_modules`, `__pycache__` | Comma-separated dir names to exclude. |

Other schema fields (e.g. `language.default_max_depth`, `language.preferred_languages`, `max_results_default`) can be set via env using the same pattern (`MCP_TS_LANGUAGE_DEFAULT_MAX_DEPTH`, etc.) if the code applies them in `config_env.update_config_from_env`. See `config_schema.py` and `config_env.py` for the full set.

---

## Adding a New Language

To add support for a new language in the MCP Tree-sitter server:

1. **Tree-sitter grammar**  
   Ensure a tree-sitter grammar for the language is available (e.g. as a Python package like `tree-sitter-<lang>` or installable from a repo). The server uses the `tree_sitter` Python binding and language objects built from these grammars.

2. **Language data module**  
   Add a new file under `src/mcp_server_tree_sitter/language/data/` named by language id, e.g. `<lang_id>.py` (e.g. `ruby.py`).

3. **Implement LanguageDataBase**  
   In that file, define a class that subclasses `LanguageDataBase` (from `language.schema`) and set the required class attributes:
   - **id** (str): e.g. `"ruby"`
   - **extensions** (list[str]): e.g. `["rb"]`
   - **scope_node_types** (dict): keys exactly `"function"`, `"class"`, `"module"`; values are lists of tree-sitter node type names for that scope kind
   - **query_templates** (dict[str, str]): named templates (e.g. `"functions"`, `"classes"`, `"imports"`) to tree-sitter query strings  
   Optionally set **node_type_descriptions**, **default_symbol_types**, **complexity_nodes**. See `language/schema.py` and existing files (e.g. `python.py`, `javascript.py`) in `language/data/`.

4. **Registration**  
   No separate registration step is needed. The loader discovers all modules in `language/data/` and registers every `LanguageDataBase` subclass. Restart the server so it loads the new module.

5. **Wire the parser**  
   Ensure the language is obtainable from the language registry (e.g. the registry or grammar loader knows how to build the tree-sitter `Language` for this id). This may require adding the grammar package to dependencies and/or a small hook in the registry/loader code depending on how your project resolves languages.

6. **Tests and lint**  
   Run the test suite and linters. Add tests for the new language if applicable.

For the exact schema and conventions, see the [per-language data README](../src/mcp_server_tree_sitter/language/data/README.md) and [LANGUAGE_COVERAGE.md](../src/mcp_server_tree_sitter/language/data/LANGUAGE_COVERAGE.md).
