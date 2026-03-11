"""Tests for loading and validating all language data from language/data/."""

from mcp_server_tree_sitter.language.loader import (
    get_extension_map,
    get_query_templates,
    get_scope_node_types,
    load_all_language_data,
)
from mcp_server_tree_sitter.language.schema import LanguageData


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
        assert isinstance(lang_data.node_type_descriptions, dict), (
            f"{lang_id}: node_type_descriptions must be a dict"
        )


def test_derived_caches_consistent_with_loaded() -> None:
    """Derived caches (scope types, extension map, query templates) match loaded language ids."""
    loaded = load_all_language_data()
    loaded_ids = set(loaded.keys())
    scope = get_scope_node_types()
    for kind in ("function", "class", "module"):
        assert set(scope[kind].keys()) == loaded_ids, (
            f"scope_node_types[{kind}] should have same keys as loaded"
        )
    ext_map = get_extension_map()
    ext_lang_ids = set(ext_map.values())
    assert ext_lang_ids <= loaded_ids, "Extension map should only reference loaded language ids"
    templates = get_query_templates()
    assert set(templates.keys()) == loaded_ids, "query_templates should have same keys as loaded"
