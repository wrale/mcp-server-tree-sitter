"""Language registry for tree-sitter languages."""

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple

from tree_sitter_language_pack import get_binding, get_language, get_parser

from ..cache.parser_cache import get_cached_parser
from ..config import CONFIG
from ..exceptions import LanguageNotFoundError
from ..utils.tree_sitter_types import (
    Language,
    Parser,
    ensure_language,
)

logger = logging.getLogger(__name__)


class LanguageRegistry:
    """Manages tree-sitter language parsers."""

    _instance: Optional["LanguageRegistry"] = None
    _lock = threading.RLock()

    def __new__(cls) -> "LanguageRegistry":
        """Singleton pattern to ensure one registry instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LanguageRegistry, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        """Initialize the registry if not already initialized."""
        with self._lock:
            if getattr(self, "_initialized", False):
                return

            self.languages: Dict[str, Language] = {}
            self._initialized = True
            self._language_map = {
                "py": "python",
                "js": "javascript",
                "ts": "typescript",
                "jsx": "javascript",
                "tsx": "typescript",
                "rb": "ruby",
                "rs": "rust",
                "go": "go",
                "java": "java",
                "c": "c",
                "cpp": "cpp",
                "cc": "cpp",
                "h": "c",
                "hpp": "cpp",
                "cs": "c_sharp",
                "php": "php",
                "scala": "scala",
                "swift": "swift",
                "kt": "kotlin",
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

            # Pre-load preferred languages if configured
            for lang in CONFIG.language.preferred_languages:
                try:
                    self.get_language(lang)
                except Exception as e:
                    logger.warning(f"Failed to pre-load language {lang}: {e}")

    def language_for_file(self, file_path: str) -> Optional[str]:
        """
        Detect language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language identifier or None if unknown
        """
        ext = file_path.split(".")[-1].lower() if "." in file_path else ""
        return self._language_map.get(ext)

    def list_available_languages(self) -> List[str]:
        """
        List languages that are installed and available.

        Returns:
            List of available language identifiers
        """
        available: List[str] = []

        # Check currently loaded languages
        available.extend(self.languages.keys())

        # Add languages available in tree-sitter-language-pack
        try:
            # Get all language names from the language pack binding
            # Type ignore required because tree-sitter-language-pack has restrictive
            # literal types but supports dynamic language names at runtime
            binding = get_binding()  # type: ignore
            if hasattr(binding, "get_all_language_names"):
                # Use the language pack's API if available
                available.extend(binding.get_all_language_names())
            else:
                # Fallback: Try common languages (we know language-pack includes these)
                for lang in self._language_map.values():
                    if lang not in available:
                        try:
                            # Type ignore required for dynamic language access pattern
                            get_language(lang)  # type: ignore
                            available.append(lang)
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Error checking language pack languages: {e}")

        return sorted(set(available))  # Use set to remove duplicates

    def list_installable_languages(self) -> List[Tuple[str, str]]:
        """
        List languages that can be installed.

        Returns:
            List of tuples (language_id, package_name)
        """
        # All languages are already available via language pack
        # This method is maintained for backward compatibility
        return []

    def install_language(self, language_name: str) -> bool:
        """
        No longer needed with tree-sitter-language-pack but maintained for
        compatibility.

        Args:
            language_name: Language identifier

        Returns:
            True if language is available

        Raises:
            LanguageNotFoundError: If language is not available
        """
        # Try to get the language to see if it's available
        try:
            self.get_language(language_name)
            return True
        except Exception as e:
            raise LanguageNotFoundError(
                f"Language {language_name} not available in tree-sitter-language-pack: "
                f"{e}"
            ) from e

    def get_language(
        self, language_name: str, auto_install: Optional[bool] = None
    ) -> Any:
        """
        Get or load a language by name.

        Args:
            language_name: Language identifier
            auto_install: DEPRECATED - No longer used with language pack

        Returns:
            Tree-sitter Language object

        Raises:
            LanguageNotFoundError: If language cannot be loaded
        """
        with self._lock:
            if language_name in self.languages:
                return self.languages[language_name]

            try:
                # Get language from language pack
                # Type ignore: language_name is dynamic but tree-sitter-language-pack
                # types expect a Literal with specific language names
                language_obj = get_language(language_name)  # type: ignore

                # Cast to our Language type for type safety
                language = ensure_language(language_obj)
                self.languages[language_name] = language
                return language
            except Exception as e:
                raise LanguageNotFoundError(
                    f"Language {language_name} not available via "
                    f"tree-sitter-language-pack: {e}"
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
            # Try to get a parser directly from the language pack
            # Type ignore: language_name is dynamic but tree-sitter-language-pack
            # types expect a Literal with specific language names
            parser = get_parser(language_name)  # type: ignore
            return parser
        except Exception:
            # Fall back to older method
            language = self.get_language(language_name)
            return get_cached_parser(language)
