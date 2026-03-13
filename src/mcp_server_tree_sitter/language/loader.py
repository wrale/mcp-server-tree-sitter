"""Load and validate per-language data from language/data/ modules.

Subclasses of LanguageDataBase register themselves when defined. LanguageDataLoader
imports all modules in the data package (so classes are created), then builds
LanguageData from the registry. Derived structures are built from the cached load.

Public API (stable): load_all_language_data, get_all_language_data, get_language_data,
get_default_symbol_types, get_scope_node_types, get_extension_map,
get_language_to_extension_map, get_query_templates, get_node_type_descriptions,
get_query_adaptation_map.
"""

import importlib
import logging
import pkgutil
from types import ModuleType
from typing import ClassVar

from .schema import DEFAULT_SYMBOL_TYPES, LanguageData, LanguageDataBase

logger: logging.Logger = logging.getLogger(__name__)

_DATA_PACKAGE: str = "mcp_server_tree_sitter.language.data"


class LanguageDataLoader:
    """Loads language data from language/data/ and builds derived structures. Cache is on the class.
    Derived structures are built once at load time; getters are accessors only.
    """

    _loaded: ClassVar[dict[str, LanguageData] | None] = None
    _scope_node_types: ClassVar[dict[str, dict[str, list[str]]] | None] = None
    _extension_map: ClassVar[dict[str, str] | None] = None
    _language_to_extension: ClassVar[dict[str, str] | None] = None
    _query_templates: ClassVar[dict[str, dict[str, str]] | None] = None
    _node_type_descriptions: ClassVar[dict[str, dict[str, str]] | None] = None
    _query_adaptation: ClassVar[dict[tuple[str, str], dict[str, str]] | None] = None

    @classmethod
    def _get_loaded(cls) -> dict[str, LanguageData]:
        """Return loaded language data, loading and caching once."""
        if cls._loaded is None:
            cls.load_all_language_data()
        assert cls._loaded is not None  # set by load_all_language_data()
        return cls._loaded

    @classmethod
    def _populate_derived_caches(cls, loaded: dict[str, LanguageData]) -> None:
        """Build and cache derived structures from loaded data. Called at load time."""
        scope: dict[str, dict[str, list[str]]] = {"function": {}, "class": {}, "module": {}}
        for lang_id, data in loaded.items():
            for kind, node_types in data.scope_node_types.items():
                scope[kind][lang_id] = list(node_types)
        cls._scope_node_types = scope

        ext_map: dict[str, str] = {}
        lang_to_ext: dict[str, str] = {}
        for data in loaded.values():
            for ext in data.extensions:
                ext_map[ext] = data.id
            if data.extensions and data.id not in lang_to_ext:
                lang_to_ext[data.id] = data.extensions[0]
        cls._extension_map = ext_map
        cls._language_to_extension = lang_to_ext

        cls._query_templates = {lang_id: dict(data.query_templates) for lang_id, data in loaded.items()}
        cls._node_type_descriptions = {lang_id: dict(data.node_type_descriptions) for lang_id, data in loaded.items()}

    @classmethod
    def load_all_language_data(cls) -> dict[str, LanguageData]:
        """
        Import all language/data modules (so LanguageDataBase subclasses register),
        then build and return a dict mapping language id -> LanguageData. Caches on the class.
        Also builds and caches derived structures (scope node types, extension map, etc.).
        """
        try:
            pkg: ModuleType = importlib.import_module(_DATA_PACKAGE)
        except ImportError as e:
            logger.warning("Language data package %s not importable: %s", _DATA_PACKAGE, e)
            cls._loaded = {}
            cls._populate_derived_caches(cls._loaded)
            return {}

        path: list[str] | None = getattr(pkg, "__path__", None)
        if path is None:
            cls._loaded = {}
            cls._populate_derived_caches(cls._loaded)
            return {}

        prefix: str = pkg.__name__ + "."
        for _importer, modname, _is_pkg in pkgutil.iter_modules(path, prefix):
            try:
                importlib.import_module(modname)
            except Exception as e:
                logger.warning("Skipping language data module %s: %s", modname, e)

        result: dict[str, LanguageData] = {}
        for reg_cls in LanguageDataBase.registered_subclasses():
            try:
                data: LanguageData = reg_cls.to_language_data()
                result[data.id] = data
            except Exception as e:
                logger.warning(
                    "Invalid language data in %s: %s",
                    f"{reg_cls.__module__}.{reg_cls.__qualname__}",
                    e,
                )
        cls._loaded = result
        cls._populate_derived_caches(cls._loaded)
        return result

    @classmethod
    def get_language_data(cls, language_id: str) -> LanguageData | None:
        """Return LanguageData for the given language id, or None if not found (cached at load time)."""
        return cls._get_loaded().get(language_id)

    @classmethod
    def get_default_symbol_types(cls, language_id: str) -> list[str]:
        """Return default symbol types for the language, or canonical default if not found (cached)."""
        data = cls._get_loaded().get(language_id)
        return list(data.default_symbol_types) if data else list(DEFAULT_SYMBOL_TYPES)

    @classmethod
    def get_all_language_data(cls) -> dict[str, LanguageData]:
        """Return all loaded language data as language id -> LanguageData (cached at load time)."""
        return cls._get_loaded()

    @classmethod
    def get_scope_node_types(cls) -> dict[str, dict[str, list[str]]]:
        """Return scope kind -> language id -> list of node type names (cached at load time)."""
        cls._get_loaded()
        assert cls._scope_node_types is not None
        return cls._scope_node_types

    @classmethod
    def get_extension_map(cls) -> dict[str, str]:
        """Return file extension -> language id (cached at load time)."""
        cls._get_loaded()
        assert cls._extension_map is not None
        return cls._extension_map

    @classmethod
    def get_language_to_extension_map(cls) -> dict[str, str]:
        """Return language id -> primary file extension (cached at load time)."""
        cls._get_loaded()
        assert cls._language_to_extension is not None
        return cls._language_to_extension

    @classmethod
    def get_query_templates(cls) -> dict[str, dict[str, str]]:
        """Return language id -> template name -> query string (cached at load time)."""
        cls._get_loaded()
        assert cls._query_templates is not None
        return cls._query_templates

    @classmethod
    def get_node_type_descriptions(cls) -> dict[str, dict[str, str]]:
        """Return language id -> node type -> description (cached at load time)."""
        cls._get_loaded()
        assert cls._node_type_descriptions is not None
        return cls._node_type_descriptions

    @classmethod
    def get_query_adaptation_map(cls) -> dict[tuple[str, str], dict[str, str]]:
        """Return (from_lang, to_lang) -> { node_type -> node_type } for query adaptation (cached)."""
        if cls._query_adaptation is None:
            try:
                mod = importlib.import_module(f"{_DATA_PACKAGE}.query_adaptation")
                cls._query_adaptation = getattr(mod, "QUERY_ADAPTATION", {})
            except Exception as e:
                logger.warning("Could not load query adaptation data: %s", e)
                cls._query_adaptation = {}
        return cls._query_adaptation


# Public API: keep the same names so callers can import functions unchanged.
def load_all_language_data() -> dict[str, LanguageData]:
    """Load all language data (cached). See LanguageDataLoader.load_all_language_data."""
    return LanguageDataLoader.load_all_language_data()


def get_all_language_data() -> dict[str, LanguageData]:
    """Return all loaded language data (cached). See LanguageDataLoader.get_all_language_data."""
    return LanguageDataLoader.get_all_language_data()


def get_language_data(language_id: str) -> LanguageData | None:
    """Return LanguageData for the given language id, or None if not found. See LanguageDataLoader.get_language_data."""
    return LanguageDataLoader.get_language_data(language_id)


def get_default_symbol_types(language_id: str) -> list[str]:
    """Default symbol types for the language, or canonical default if not found."""
    return LanguageDataLoader.get_default_symbol_types(language_id)


def get_scope_node_types() -> dict[str, dict[str, list[str]]]:
    """Build scope node types from loaded data. See LanguageDataLoader.get_scope_node_types."""
    return LanguageDataLoader.get_scope_node_types()


def get_extension_map() -> dict[str, str]:
    """Build extension -> language id map. See LanguageDataLoader.get_extension_map."""
    return LanguageDataLoader.get_extension_map()


def get_language_to_extension_map() -> dict[str, str]:
    """Language id -> primary file extension. See LanguageDataLoader.get_language_to_extension_map."""
    return LanguageDataLoader.get_language_to_extension_map()


def get_query_templates() -> dict[str, dict[str, str]]:
    """Build query templates by language. See LanguageDataLoader.get_query_templates."""
    return LanguageDataLoader.get_query_templates()


def get_node_type_descriptions() -> dict[str, dict[str, str]]:
    """Build node type descriptions by language. See LanguageDataLoader.get_node_type_descriptions."""
    return LanguageDataLoader.get_node_type_descriptions()


def get_query_adaptation_map() -> dict[tuple[str, str], dict[str, str]]:
    """Return query adaptation map (from_lang, to_lang) -> node_type mapping."""
    return LanguageDataLoader.get_query_adaptation_map()
