# Per-language data directory

One **Python module per supported language** lives here. Each module defines a class that subclasses `LanguageDataBase` in `language/schema.py`; the loader discovers these modules and builds validated `LanguageData` from them at startup.

## Layout

- **One file per language**, named by language id: `python.py`, `javascript.py`, `csharp.py`, etc.
- Each module defines a **class** that subclasses `LanguageDataBase` and sets class attributes: `id`, `extensions`, `scope_node_types`, `query_templates`, and optionally `node_type_descriptions`. The loader calls `to_language_data()` to validate and build a `LanguageData` instance.

## Required structure (LanguageDataBase class attributes)

| Field                    | Type           | Required  | Description                                                                                            |
|--------------------------|----------------|-----------|--------------------------------------------------------------------------------------------------------|
| `id`                     | str            | Yes       | Language identifier (e.g. `"python"`, `"javascript"`).                                                 |
| `extensions`             | list[str]      | Yes       | At least one file extension mapping to this language (e.g. `["py"]`).                                  |
| `scope_node_types`       | dict           | Yes       | Keys exactly `"function"`, `"class"`, `"module"`. Each value is a list of tree-sitter node type names. |
| `query_templates`        | dict[str, str] | Yes       | Template name → tree-sitter query string (multi-line allowed).                                         |
| `node_type_descriptions` | dict[str, str] | No        | Node type name → short description; default `{}`.                                                      |
| `complexity_nodes`       | list[str]      | No        | Tree-sitter node types for cyclomatic complexity (e.g. if_statement); default `[]`.                    |

See [LANGUAGE_COVERAGE.md](LANGUAGE_COVERAGE.md) in this directory for the coverage table (Extensions, Templates, get_enclosing_scope, Complexity nodes) for all pack languages.

## Convention

- **File name** should match `id` (e.g. `id: "python"` → `python.py`). The loader discovers all modules in this package via `pkgutil.iter_modules` and registers each `LanguageDataBase` subclass.
- **Scope kinds** must be exactly `function`, `class`, `module` (see `ScopeKind` in `scope_node_types.py`).
- Keep modules as data only: class attributes and no executable logic beyond the class definition.

## Adding a new language

1. Add a new module `language/data/<lang_id>.py`.
2. Define a class that subclasses `LanguageDataBase` and set the required (and optional) class attributes. Copy an existing file (e.g. `python.py`) and adapt to the grammar.
3. No separate registration step is needed; the loader imports all modules in this package and uses `LanguageDataBase.registered_subclasses()`.
4. Run tests and linting.
