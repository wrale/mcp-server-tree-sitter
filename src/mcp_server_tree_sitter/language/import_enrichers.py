"""Optional per-language import enrichers for symbols and dependency discovery.

Language data modules (e.g. language/data/python.py) can register enrichers that run
extra queries and add aliased/supplementary imports. Tools call get_*_enricher(language)
and invoke the callback if present.
"""

from typing import Any, Callable, Dict

from ..utils.tree_sitter_types import Node


def node_location(node: Node) -> Dict[str, Dict[str, int]]:
    """Build a location dict from a tree-sitter node for use in enricher callbacks."""
    return {
        "start": {"row": node.start_point[0], "column": node.start_point[1]},
        "end": {"row": node.end_point[0], "column": node.end_point[1]},
    }


# Language id -> (symbols, safe_lang, tree, source_bytes) -> None
_SymbolImportEnricher = Callable[[Dict[str, list], Any, Any, bytes], None]  # noqa: ANN401
# Language id -> (module_imports, safe_lang, tree, source_bytes) -> None
_DependencyModuleEnricher = Callable[[set[str], Any, Any, bytes], None]  # noqa: ANN401

_symbol_enrichers: Dict[str, _SymbolImportEnricher] = {}
_dependency_enrichers: Dict[str, _DependencyModuleEnricher] = {}


def register_symbol_import_enricher(language_id: str, fn: _SymbolImportEnricher) -> None:
    """Register a callback to add extra import symbols for a language (e.g. aliased imports)."""
    _symbol_enrichers[language_id] = fn


def get_symbol_import_enricher(language_id: str) -> _SymbolImportEnricher | None:
    """Return the symbol import enricher for the language, or None."""
    return _symbol_enrichers.get(language_id)


def register_dependency_module_enricher(language_id: str, fn: _DependencyModuleEnricher) -> None:
    """Register a callback to add extra module names to dependency discovery for a language."""
    _dependency_enrichers[language_id] = fn


def get_dependency_module_enricher(language_id: str) -> _DependencyModuleEnricher | None:
    """Return the dependency module enricher for the language, or None."""
    return _dependency_enrichers.get(language_id)
