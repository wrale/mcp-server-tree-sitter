# Critical Next Steps

This document outlines the critical refactoring steps needed to address the remaining issues in the MCP Tree-sitter Server project.

## Current Status

We've made significant progress in fixing linting issues and implementing key features. The following work has been completed:

1. ✅ Created a dedicated tree-sitter type handling module (`utils/tree_sitter_types.py`)
2. ✅ Updated `cache/parser_cache.py` to use the new typing utilities
3. ✅ Updated `language/registry.py` to use the new typing utilities
4. ✅ Created file I/O utilities (`utils/file_io.py`)
5. ✅ Fixed analysis.py file operations
6. ✅ Created tree-sitter API helper functions (`utils/tree_sitter_helpers.py`)
7. ✅ Added TreeCursor protocol to `utils/tree_sitter_types.py`
8. ✅ Created cursor helper functions in `utils/tree_sitter_helpers.py`
9. ✅ Extended `cache/parser_cache.py` to track tree modification state
10. ✅ Implemented tree editing methods in `utils/tree_sitter_helpers.py`
11. ✅ Added support for changed_ranges detection
12. ✅ Created a context utility module (`utils/context/mcp_context.py`)
13. ✅ Added progress reporting infrastructure to long-running operations
14. ✅ Implemented context-aware methods for tools
15. ✅ Created `capabilities/server_capabilities.py` for capability declaration
16. ✅ Added resource subscription support
17. ✅ Added completion suggestions support
18. ✅ Fixed type-checking issues in tree-sitter protocol interfaces
19. ✅ Fixed node type handling in cursor traversal for null safety
20. ✅ Fixed type annotations for query captures in analysis tools

## Immediate Next Steps

The following tasks need to be addressed next:

1. 🔄 **Integrate tree-sitter-language-pack for Language Support**
   - Replace individual language parser dependencies with tree-sitter-language-pack
   - Update language registry to use language pack API
   - Fix language detection and loading mechanisms
   - Update related tools to use the new API consistently
   - See [Appendix: Language Pack Integration](#appendix-language-pack-integration) for details

2. 🔄 **Implement Cursor-based AST Traversal in Models**
   - Update `models/ast.py` to use cursor-based tree traversal for efficiency
   - Replace recursive traversal with more efficient cursor-based navigation
   - Add helper functions to simplify common traversal patterns
   - Handle null nodes safely throughout traversal code

3. 🔄 **Implement Additional Testing**
   - Implement additional test cases for the tree-sitter utilities
   - Add tests for context utilities and progress reporting
   - Test incremental parsing with various code changes
   - Create test cases for tree cursor traversal
   - Add tests for tree-sitter type safety mechanisms

4. 🔄 **Enhance Claude Desktop Integration**
   - Complete environment variable handling
   - Enhance integration with Claude UX
   - Add user-friendly error messages for common issues
   - Improve documentation for Claude Desktop integration

5. 🔄 **Documentation Updates**
   - Update docstrings to reflect type safety improvements
   - Create detailed documentation for tree-sitter typing strategy
   - Document common patterns for tree traversal using cursors
   - Add examples of best practices for tree-sitter interaction

Once these items are completed, CRITICAL-NEXT-STEPS.md can be deprecated.

## Implementation Details

### Tree-sitter Type Safety

The tree-sitter type handling has been significantly improved:
- Added appropriate interfaces via Protocol classes
- Implemented safe type casting with runtime verification
- Added null-safety checks throughout cursor traversal code
- Used targeted type suppressions for API compatibility issues
- Added clear documentation for type handling patterns

### TreeCursor Enhancements

The TreeCursor API implementation now provides:
- Type-safe cursor traversal with proper Optional type handling
- Null-safe navigation through node children and siblings
- Efficient collector patterns for gathering nodes
- Better handling of potential runtime type variations
- Safe parent-child relationship traversal

### Type-Safe Query Handling

Query processing now includes:
- Explicit type casting for query captures
- Safe unpacking of node-capture pairs
- Better error handling for malformed queries
- Type-safe processing of query results

Remaining implementation details from the previous version are still applicable.

## Conclusion

Our recent improvements have significantly enhanced type safety and robustness when interacting with the tree-sitter library. The remaining tasks focus on extending these patterns to other parts of the codebase and ensuring comprehensive testing.

With the type-checking issues largely resolved, we can now focus on improving efficiency through cursor-based traversal in all parts of the codebase and enhancing the testing coverage to ensure long-term stability.

Once these immediate next steps are completed, we can move on to the additional feature improvements outlined in the ROADMAP.md document.

## Appendix: Language Pack Integration

### Problem Statement

The current implementation attempts to import individual tree-sitter language modules (e.g., `tree_sitter_python`), which causes failures when these modules are not installed. The auto-installation mechanism is disabled by default, and even when enabled, it requires server restarts after installing each language module.

### Solution: tree-sitter-language-pack

The [tree-sitter-language-pack](https://github.com/Goldziher/tree-sitter-language-pack) package provides a comprehensive collection of 100+ tree-sitter languages in a single package with pre-built wheels. It offers a clean API to access language parsers without requiring individual installations.

### Implementation Steps

1. **Update Dependencies**
   - Add `tree-sitter-language-pack` to dependencies in `pyproject.toml`
   - Remove individual language parser dependencies from `[project.optional-dependencies]`

2. **Modify Language Registry**
   - Update `src/mcp_server_tree_sitter/language/registry.py` to use the language pack API:
     - Replace direct imports with `from tree_sitter_language_pack import get_language, get_parser`
     - Update `get_language()` method to use `get_language()` from the language pack
     - Update `get_parser()` method to use `get_parser()` from the language pack

3. **Update Configuration**
   - Modify `config.py` to remove `auto_install` option (no longer needed)
   - Add configuration for language pack preferences if necessary

4. **Update Related Code**
   - Fix any code that references individual language modules
   - Update error handling for language loading to reflect new approach
   - Ensure all language loading uses the language pack consistently

5. **Testing and Documentation**
   - Test language detection and loading with various file types
   - Update documentation to reference language pack instead of individual modules
   - Add information about available languages to user documentation

This approach will simplify the codebase, improve reliability, and provide access to a much wider range of languages without requiring individual installations or server restarts.

### Example Implementation

Here's a draft implementation of the modified language registry:

```python
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
            # Add any languages already loaded via language pack
            # This is just a sample pattern as the actual API might differ
            pass  # No clean way to get list from language pack without trying every language
        except Exception as e:
            logger.warning(f"Error checking language pack languages: {e}")

        return sorted(available)

    def list_installable_languages(self) -> List[Tuple[str, str]]:
        """
        List languages that can be installed.

        Returns:
            List of tuples (language_id, package_name)
        """
        # All languages are already available via language pack
        # This method is maintained for backward compatibility
        return []

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
                language_obj = get_language(language_name)
                
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
            # Try to get a parser directly from the language pack
            parser = get_parser(language_name)
            return parser
        except Exception:
            # Fall back to older method
            language = self.get_language(language_name)
            return get_cached_parser(language)
```
