"""Tests for loading and validating all language data from language/data/."""

from mcp_server_tree_sitter.language.loader import (
    get_default_symbol_types,
    get_extension_map,
    get_query_templates,
    get_scope_node_types,
    load_all_language_data,
)
from mcp_server_tree_sitter.language.schema import DEFAULT_SYMBOL_TYPES, LanguageData


def test_load_all_language_data_returns_non_empty() -> None:
    """Loading language data yields at least one language."""
    data = load_all_language_data()
    assert isinstance(data, dict)
    assert len(data) >= 1, "Expected at least one language from language/data/"
    for lang_id, lang_data in data.items():
        assert isinstance(lang_data, LanguageData)
        assert lang_data.id == lang_id


def test_each_language_data_valid() -> None:
    """Each loaded language has required fields and valid scope kinds."""
    data = load_all_language_data()
    required_scope_kinds = {"function", "class", "module"}
    for lang_id, lang_data in data.items():
        assert lang_id
        assert lang_data.extensions, f"{lang_id}: extensions must be non-empty"
        assert set(lang_data.scope_node_types.keys()) == required_scope_kinds, (
            f"{lang_id}: scope_node_types must have exactly {required_scope_kinds}"
        )
        assert isinstance(lang_data.query_templates, dict), f"{lang_id}: query_templates must be a dict"
        assert isinstance(lang_data.node_type_descriptions, dict), f"{lang_id}: node_type_descriptions must be a dict"
        assert isinstance(lang_data.default_symbol_types, list), f"{lang_id}: default_symbol_types must be a list"


def test_derived_caches_consistent_with_loaded() -> None:
    """Derived caches (scope types, extension map, query templates) match loaded language ids."""
    loaded = load_all_language_data()
    loaded_ids = set(loaded.keys())
    scope = get_scope_node_types()
    for kind in ("function", "class", "module"):
        assert set(scope[kind].keys()) == loaded_ids, f"scope_node_types[{kind}] should have same keys as loaded"
    ext_map = get_extension_map()
    ext_lang_ids = set(ext_map.values())
    assert ext_lang_ids <= loaded_ids, "Extension map should only reference loaded language ids"
    templates = get_query_templates()
    assert set(templates.keys()) == loaded_ids, "query_templates should have same keys as loaded"


def test_get_default_symbol_types_returns_per_language_defaults() -> None:
    """get_default_symbol_types returns the configured list for known languages."""
    assert get_default_symbol_types("python") == ["functions", "classes", "imports"]
    assert get_default_symbol_types("rust") == ["functions", "structs", "imports"]
    assert get_default_symbol_types("cpp") == ["functions", "classes", "structs", "imports"]
    assert get_default_symbol_types("julia") == ["functions", "modules", "structs", "imports"]


def test_get_default_symbol_types_returns_canonical_default_for_unknown() -> None:
    """get_default_symbol_types returns DEFAULT_SYMBOL_TYPES for unknown language."""
    result = get_default_symbol_types("unknown_lang_xyz_123")
    assert result == DEFAULT_SYMBOL_TYPES
    # Return value should be a copy so mutating does not affect the constant
    result.append("other")
    assert get_default_symbol_types("unknown_lang_xyz_123") == DEFAULT_SYMBOL_TYPES
