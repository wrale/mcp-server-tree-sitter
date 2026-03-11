"""Language registry for tree-sitter languages."""

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple, cast

from tree_sitter_language_pack import get_language, get_parser

# Import parser_cache functions inside methods to avoid circular imports
# Import global_context inside methods to avoid circular imports
from ..exceptions import LanguageNotFoundError
from ..utils.tree_sitter_types import (
    Language,
    Parser,
    ensure_language,
)

logger = logging.getLogger(__name__)

# Fallback extension -> language id for extensions not in per-language data (e.g. ruby, json).
# Loader provides map from language/data/; this covers tree-sitter-language-pack languages
# we don't yet have as data files.
_EXTENSION_FALLBACK: Dict[str, str] = {
    "rb": "ruby",
    "php": "php",
    "scala": "scala",
    "lua": "lua",
    "hs": "haskell",
    "ml": "ocaml",
    "sh": "bash",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
    "md": "markdown",
    "html": "html",
    "css": "css",
    "scss": "scss",
    "sass": "scss",
    "sql": "sql",
    "proto": "proto",
    "elm": "elm",
    "clj": "clojure",
    "ex": "elixir",
    "exs": "elixir",
}


class LanguageRegistry:
    """Manages tree-sitter language parsers."""

    def __init__(self) -> None:
        """Initialize the registry. Extension map comes from loader (language/data/); fallback for others."""
        self._lock = threading.RLock()
        self.languages: Dict[str, Language] = {}
        from .loader import get_extension_map

        self._language_map = dict(get_extension_map())
        for ext, lang_id in _EXTENSION_FALLBACK.items():
            if ext not in self._language_map:
                self._language_map[ext] = lang_id
            else:
                logger.warning(
                    "Extension %r from fallback (%s) already set by language data (%s) - using data",
                    ext,
                    lang_id,
                    self._language_map[ext],
                )

        # Pre-load preferred languages if configured
        # Get dependencies within the method to avoid circular imports
        try:
            from ..di import get_container

            config = get_container().get_config()
            for lang in config.language.preferred_languages:
                try:
                    self.get_language(lang)
                except Exception as e:
                    logger.warning(f"Failed to pre-load language {lang}: {e}")
        except ImportError:
            # If dependency container isn't available yet, just skip this step
            logger.warning("Skipping pre-loading of languages due to missing dependencies")

    def language_for_file(self, file_path: str) -> Optional[str]:
        """
        Detect language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language identifier or None if unknown
        """
        # Handle Path objects (WindowsPath/PosixPath) by converting to string
        file_path = str(file_path)
        ext = file_path.split(".")[-1].lower() if "." in file_path else ""
        return self._language_map.get(ext)

    def list_available_languages(self) -> List[str]:
        """
        List languages that are available via tree-sitter-language-pack.

        Returns:
            List of available language identifiers
        """
        # Start with loaded languages
        available = set(self.languages.keys())

        # Add all mappable languages from our extension map
        # These correspond to the languages available in tree-sitter-language-pack
        available.update(set(self._language_map.values()))

        # Add frequently used languages that might not be in the map
        common_languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "c",
            "cpp",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "bash",
            "html",
            "css",
            "json",
            "yaml",
            "markdown",
            "csharp",
            "objective_c",
            "xml",
        ]
        available.update(common_languages)

        # Return as a sorted list
        return sorted(available)

    def list_installable_languages(self) -> List[Tuple[str, str]]:
        """
        List languages that can be installed.
        With tree-sitter-language-pack, no additional installation is needed.

        Returns:
            Empty list (all languages are available via language-pack)
        """
        return []

    def is_language_available(self, language_name: str) -> bool:
        """
        Check if a language is available in tree-sitter-language-pack.

        Args:
            language_name: Language identifier

        Returns:
            True if language is available
        """
        try:
            self.get_language(language_name)
            return True
        except Exception:
            return False

    def get_language(self, language_name: str) -> Language:
        """
        Get or load a language by name from tree-sitter-language-pack.

        Args:
            language_name: Language identifier

        Returns:
            Tree-sitter Language object

        Raises:
            LanguageNotFoundError: If language cannot be loaded
        """
        with self._lock:
            if language_name in self.languages:
                return self.languages[language_name]

            try:
                # Get language from language pack (pack expects Literal language name; we pass str)
                language_obj = get_language(cast(Any, language_name))

                # Cast to our Language type for type safety
                language = ensure_language(language_obj)
                self.languages[language_name] = language
                return language
            except Exception as e:
                raise LanguageNotFoundError(
                    f"Language {language_name} not available via tree-sitter-language-pack: {e}"
                ) from e

    def get_parser(self, language_name: str) -> Parser:
        """
        Get a parser for the specified language.

        Args:
            language_name: Language identifier

        Returns:
            Tree-sitter Parser configured for the language
        """
        try:
            # Try to get a parser directly from the language pack (pack expects Literal language name)
            parser = get_parser(cast(Any, language_name))
            return parser
        except Exception:
            # Fall back to older method, importing at runtime to avoid circular imports
            from ..cache.parser_cache import get_cached_parser

            language = self.get_language(language_name)
            return get_cached_parser(language)
