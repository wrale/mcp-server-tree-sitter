"""Language registry for tree-sitter languages."""

import importlib
import logging
import subprocess
import threading
from typing import Any, Dict, List, Optional, Tuple

from ..cache.parser_cache import get_cached_parser
from ..config import CONFIG
from ..exceptions import LanguageInstallError, LanguageNotFoundError

try:
    import pkg_resources  # type: ignore
    from tree_sitter import Language as TSLanguage
    from tree_sitter import Parser as TSParser
except ImportError:
    # For type checking and module importing without tree-sitter installed
    pkg_resources = None

    class TSLanguage:
        pass

    class TSParser:
        def set_language(self, language: Any) -> None:
            pass


# Type aliases for better readability
Language = TSLanguage
Parser = TSParser

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

    def get_package_name(self, language_name: str) -> str:
        """
        Get the Python package name for a language.

        Args:
            language_name: Language identifier

        Returns:
            Python package name
        """
        return f"tree-sitter-{language_name.replace('_', '-')}"

    def list_available_languages(self) -> List[str]:
        """
        List languages that are installed and available.

        Returns:
            List of available language identifiers
        """
        available: List[str] = []

        # Check currently loaded languages
        available.extend(self.languages.keys())

        # Look for installed packages
        if pkg_resources:
            for package in pkg_resources.working_set:
                if package.key.startswith("tree-sitter-"):
                    lang_name = package.key[len("tree-sitter-") :].replace("-", "_")
                    if lang_name not in available:
                        available.append(lang_name)

        return sorted(available)

    def list_installable_languages(self) -> List[Tuple[str, str]]:
        """
        List languages that can be installed.

        Returns:
            List of tuples (language_id, package_name)
        """
        # This is a selection of commonly used languages
        # In a real implementation, this could query PyPI
        installable = [
            ("python", "tree-sitter-python"),
            ("javascript", "tree-sitter-javascript"),
            ("typescript", "tree-sitter-typescript"),
            ("ruby", "tree-sitter-ruby"),
            ("rust", "tree-sitter-rust"),
            ("go", "tree-sitter-go"),
            ("java", "tree-sitter-java"),
            ("c", "tree-sitter-c"),
            ("cpp", "tree-sitter-cpp"),
            ("c_sharp", "tree-sitter-c-sharp"),
            ("php", "tree-sitter-php"),
        ]

        # Filter out already installed languages
        available = self.list_available_languages()
        return [(lang, pkg) for lang, pkg in installable if lang not in available]

    def install_language(self, language_name: str) -> bool:
        """
        Try to install a language parser package.

        Args:
            language_name: Language identifier

        Returns:
            True if installation succeeded

        Raises:
            LanguageInstallError: If installation fails
        """
        if not CONFIG.language.auto_install:
            raise LanguageInstallError(
                f"Automatic installation disabled. "
                f"Please install {self.get_package_name(language_name)} manually."
            )

        package = self.get_package_name(language_name)

        try:
            # Use pip to install the package
            subprocess.check_call(["pip", "install", package])
            return True
        except subprocess.CalledProcessError as e:
            raise LanguageInstallError(f"Failed to install {package}: {e}") from e

    def get_language(
        self, language_name: str, auto_install: Optional[bool] = None
    ) -> Any:
        """
        Get or load a language by name.

        Args:
            language_name: Language identifier
            auto_install: Whether to try installing missing languages

        Returns:
            Tree-sitter Language object

        Raises:
            LanguageNotFoundError: If language cannot be loaded
        """
        with self._lock:
            if language_name in self.languages:
                return self.languages[language_name]

            try:
                # Import tree-sitter language module
                module_name = f"tree_sitter_{language_name}"
                module = importlib.import_module(module_name)
                language = TSLanguage(module.language())
                self.languages[language_name] = language
                return language
            except (ImportError, AttributeError) as e:
                # Try installing if auto_install is enabled
                should_install = (
                    auto_install
                    if auto_install is not None
                    else CONFIG.language.auto_install
                )

                if should_install:
                    try:
                        success = self.install_language(language_name)
                        if success:
                            # Retry after installation
                            return self.get_language(language_name, auto_install=False)
                    except LanguageInstallError as install_err:
                        raise LanguageNotFoundError(
                            f"Language {language_name} not available "
                            f"and installation failed: {install_err}"
                        ) from install_err

                raise LanguageNotFoundError(
                    f"Language {language_name} not available: {e}"
                ) from e

    def get_parser(self, language_name: str) -> Parser:
        """
        Get a parser for the specified language.

        Args:
            language_name: Language identifier

        Returns:
            Tree-sitter Parser configured for the language
        """
        language = self.get_language(language_name)
        return get_cached_parser(language)
