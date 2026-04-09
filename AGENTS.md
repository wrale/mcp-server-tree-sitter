# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project Overview

MCP Tree-sitter Server — a Model Context Protocol server providing code analysis via tree-sitter. Python 3.10+, packaged with hatchling, managed with uv.

## Setup

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
```

## Before Committing

All of these must pass — CI enforces them:

```bash
ruff check src/               # Lint (E, F, I, W, B rules)
ruff format --check src/      # Format check
mypy src/mcp_server_tree_sitter  # Type check
pytest tests/                  # 217+ tests, must all pass
```

Or use the Makefile: `make prepare`

## Key Architecture

- **Source:** `src/mcp_server_tree_sitter/`
- **DI container:** `di.py` — constructs all dependencies; avoid circular imports with it
- **Config:** `config.py` — `ConfigurationManager` auto-loads YAML from `MCP_TS_CONFIG_PATH` or `~/.config/tree-sitter/config.yaml`. Precedence: env vars > YAML > defaults
- **Language registry:** `language/registry.py` — maps file extensions to tree-sitter-language-pack identifiers
- **Templates:** `language/templates/` — per-language query templates (one file per language)
- **Tools:** `tools/` — MCP tool implementations (analysis, search, ast_operations, file_operations)
- **Helpers:** `utils/tree_sitter_helpers.py` — includes `query_captures()` compat wrapper for tree-sitter >= 0.24

## tree-sitter API Compatibility

tree-sitter >= 0.24 removed `Query.captures()`. Always use the `query_captures(query, node)` wrapper from `utils/tree_sitter_helpers.py` instead of calling `query.captures()` directly. This applies to both source and test code.

## Adding a New Language

1. Create `language/templates/<lang>.py` with a `TEMPLATES` dict (follow existing patterns like `go.py`)
2. Register the file extension in `language/registry.py` `_language_map`
3. Import and register in `language/templates/__init__.py`
4. Add default symbol types in `tools/analysis.py` `extract_symbols()`
5. Verify the language identifier works: `from tree_sitter_language_pack import get_language; get_language("<id>")`

## Common Pitfalls

- **Circular imports with `di.py`:** The DI container constructs registries. Don't import `get_container` from `__init__` methods of objects the container creates. Use method injection instead.
- **Root logger:** Do NOT call `configure_root_logger()` at module import time. Libraries must not reconfigure the root logger.
- **`common_languages` list:** Uses tree-sitter-language-pack identifiers (e.g., `csharp` not `c_sharp`). Verify with `get_language()` before adding.
- **TypeScript grammar:** Import statements require the `import_clause` node between `import_statement` and `named_imports`/`namespace_import`.
- **Test isolation:** Some tests are order-dependent due to shared singleton state. If a test passes alone but fails in suite, check for state leakage.

## PR Process

- All PRs must pass CI (ruff check, ruff format, mypy, pytest)
- Squash merge to main
- Credit community contributors in commit messages and PR descriptions
- For dependency bumps, pin transitive deps with security floors in `pyproject.toml`

## Release Process

1. Bump version in `pyproject.toml`
2. Update README if features/languages changed
3. Merge to main, confirm CI green
4. Create GitHub release with tag `vX.Y.Z` — this triggers the release workflow which publishes to PyPI
