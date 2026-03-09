# Test Suite

Tests for the MCP Tree-sitter Server. Run with `make test` or `uv run --extra dev python -m pytest`.

`conftest.py` registers the diagnostic plugin and resets the project registry between tests. Shared helpers live in `test_helpers.py`.

---

## Configuration

| File | Purpose |
|------|---------|
| **test_basic.py** | Default config values and basic project registry; minimal smoke tests. |
| **test_config_manager.py** | `ConfigurationManager`: init, load from file, `update_value`, `to_dict`, env overrides. |
| **test_config_behavior.py** | How config (cache, security, max depth) affects real behavior (AST, file access, exclusions). |
| **test_yaml_config.py** | Loading and applying server config from YAML files (no DI). |
| **test_yaml_config_di.py** | Same as above but through the DI/configure path. |
| **test_env_config.py** | Environment variable overrides (precedence over YAML and defaults). |
| **test_cache_config.py** | Cache-specific config: enabled, size, TTL, and cache behavior under those settings. |
| **test_debug_flag.py** | Debug flag and `MCP_TS_LOG_LEVEL`; `update_log_levels` and handler sync. |

---

## Dependency injection and context

| File | Purpose |
|------|---------|
| **test_di.py** | `DependencyContainer` singleton, custom deps, and that core deps are initialized. |
| **test_context.py** | `ServerContext` / global context: init, get_config, register/list/remove project, clear cache, configure. |

---

## Logging

| File | Purpose |
|------|---------|
| **test_logging_bootstrap.py** | Logging bootstrap: import order, delegation to bootstrap, key modules using it, level updates. |
| **test_logging_config.py** | Log level configuration (without DI). |
| **test_logging_config_di.py** | Log level configuration with DI and YAML. |
| **test_logging_env_vars.py** | `MCP_TS_LOG_LEVEL` and `get_log_level_from_env` / `update_log_levels`. |
| **test_logging_early_init.py** | Logging configured early in lifecycle; env vars and handler sync at import. |
| **test_logging_handlers.py** | Handler level synchronization and multiple handlers with log streams. |

---

## Project registration and file operations

| File | Purpose |
|------|---------|
| **test_registration.py** | Tool and prompt registration: all tools/prompts registered, key tools call the right helpers. |
| **test_project_persistence.py** | Project registry singleton and persistence across MCP tool calls and server lifecycle. |
| **test_persistent_server.py** | Single MCP server instance and project registration across calls. |
| **test_file_operations.py** | `list_project_files`, `get_file_content`, `get_file_info`, line limits, security (path traversal). |

---

## Language registry and listing

| File | Purpose |
|------|---------|
| **test_language_listing.py** | `list_available_languages`, API consistency, and server language tools. |

---

## AST and tree-sitter

| File | Purpose |
|------|---------|
| **test_ast_cursor.py** | Cursor-based AST: `node_to_dict_cursor` and traversal. |
| **test_models_ast.py** | `node_to_dict`, `summarize_node`, `find_node_at_position`, `extract_node_path`; depth and text options. |
| **test_tree_sitter_helpers.py** | Parse (file/source, incremental), edit tree, changed ranges, `get_node_text`, `walk_tree`, node predicates. |

---

## Enclosing scope (get_enclosing_scope)

| File | Purpose |
|------|---------|
| **test_scope_node_types.py** | Canonical scope kind → per-language node type mapping: Python/JavaScript function/class/module and unknown language/kind. |
| **test_find_enclosing_scope.py** | Core helper find_enclosing_scope: position in function, on import (module), in class body (class). |
| **test_enclosing_scope_integration.py** | Integration: get_enclosing_scope_for_path with registered project, path, row, column. |

---

## Search, queries, and analysis

| File | Purpose |
|------|---------|
| **test_query_result_handling.py** | Query capture processing, result shape, capture types, and language-pack query execution. |
| **test_symbol_extraction.py** | Symbol extraction, dependency analysis, AST access, query-based extraction, and debug file output. |
| **test_rust_compatibility.py** | Rust: AST parsing, symbol extraction, dependency analysis, and trait/macro handling. |

---

## Server, capabilities, and CLI

| File | Purpose |
|------|---------|
| **test_server.py** | Server module: MCP server init, `configure_with_context` (cache, file size, log level, config path). |
| **test_server_capabilities.py** | Capability registration and completion suggestions (project, language, config). |
| **test_cli_arguments.py** | CLI: `--help` / `--version` / `--debug` / `--config` / `--disable-cache` and conflict handling. |

---

## Failure modes and robustness

| File | Purpose |
|------|---------|
| **test_failure_modes.py** | Invalid project, missing files, and other error paths; tree-sitter API robustness. |

---

## MCP context (progress and reporting)

| File | Purpose |
|------|---------|
| **test_mcp_context.py** | `MCPContext`, `ProgressScope`, progress reporting, logging methods, and context passthrough. |

---

## Build and tooling

| File | Purpose |
|------|---------|
| **test_makefile_targets.py** | Makefile structure: mcp-run/mcp-dev/mcp-install use `uv run mcp` and launcher; optional execution check. |

---

## Diagnostics

Diagnostic tests under `test_diagnostics/` use the `diagnostic` marker and can write results for inspection. Run with `make test-diagnostics` or `pytest tests/test_diagnostics/ -v`.

| File | Purpose |
|------|---------|
| **test_diagnostics/test_ast.py** | AST failures and language detection; diagnostic plugin usage. |
| **test_diagnostics/test_ast_parsing.py** | `get_ast` and direct parsing behavior; diagnostic output. |
| **test_diagnostics/test_cursor_ast.py** | Cursor-based AST and large-tree handling. |
| **test_diagnostics/test_language_pack.py** | tree-sitter and language-pack imports, bindings, and Python environment. |
| **test_diagnostics/test_language_registry.py** | Language detection and listing; detection vs listing consistency. |
| **test_diagnostics/test_unpacking_errors.py** | Unpacking and error handling in get_symbols, get_dependencies, analyze_complexity, run_query. |

---

## Test support

| File | Purpose |
|------|---------|
| **test_helpers.py** | Shared fixtures and helpers: project registration, AST/query/analysis helpers, temp config; used by many tests. |
