"""Caching system for tree-sitter parse trees."""

import logging
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from tree_sitter import Language as TSLanguage
    from tree_sitter import Parser as TSParser
    from tree_sitter import Tree as TSTree
except ImportError:
    # For type checking and module importing without tree-sitter installed
    TSTree = Any

    class TSLanguage:
        pass

    class TSParser:
        def set_language(self, language: Any) -> None:
            pass


from ..config import CONFIG

logger = logging.getLogger(__name__)

# Type aliases for better readability
Tree = TSTree
Language = TSLanguage
Parser = TSParser


class TreeCache:
    """Cache for parsed syntax trees."""

    def __init__(
        self, max_size_mb: Optional[int] = None, ttl_seconds: Optional[int] = None
    ):
        self.max_size_mb = max_size_mb or CONFIG.cache.max_size_mb
        self.ttl_seconds = ttl_seconds or CONFIG.cache.ttl_seconds
        self.cache: Dict[str, Tuple[Any, bytes, float]] = (
            {}
        )  # (tree, source, timestamp)
        self.lock = threading.RLock()
        self.current_size_bytes = 0

    def _get_cache_key(self, file_path: Path, language: str) -> str:
        """Generate cache key from file path and language."""
        return f"{language}:{str(file_path)}:{file_path.stat().st_mtime}"

    def get(self, file_path: Path, language: str) -> Optional[Tuple[Any, bytes]]:
        """
        Get cached tree if available and not expired.

        Args:
            file_path: Path to the source file
            language: Language identifier

        Returns:
            Tuple of (tree, source_bytes) if cached, None otherwise
        """
        if not CONFIG.cache.enabled:
            return None

        try:
            cache_key = self._get_cache_key(file_path, language)
        except (FileNotFoundError, OSError):
            return None

        with self.lock:
            if cache_key in self.cache:
                tree, source, timestamp = self.cache[cache_key]

                # Check if cache entry has expired
                if time.time() - timestamp > self.ttl_seconds:
                    del self.cache[cache_key]
                    # Approximate size reduction
                    self.current_size_bytes -= len(source)
                    return None

                return tree, source

        return None

    def put(self, file_path: Path, language: str, tree: Any, source: bytes) -> None:
        """
        Cache a parsed tree.

        Args:
            file_path: Path to the source file
            language: Language identifier
            tree: Parsed tree
            source: Source bytes
        """
        if not CONFIG.cache.enabled:
            return

        try:
            cache_key = self._get_cache_key(file_path, language)
        except (FileNotFoundError, OSError):
            return

        source_size = len(source)

        # Check if adding this entry would exceed cache size limit
        if source_size > self.max_size_mb * 1024 * 1024:
            logger.warning(
                f"File too large to cache: {file_path} "
                f"({source_size / (1024*1024):.2f}MB)"
            )
            return

        with self.lock:
            # If we need to make room, remove oldest entries
            if self.current_size_bytes + source_size > self.max_size_mb * 1024 * 1024:
                self._evict_entries(source_size)

            # Store the new entry
            self.cache[cache_key] = (tree, source, time.time())
            self.current_size_bytes += source_size

    def _evict_entries(self, required_bytes: int) -> None:
        """
        Evict entries to make room for new data.

        Args:
            required_bytes: Number of bytes to make room for
        """
        # Sort by timestamp (oldest first)
        sorted_entries = sorted(
            self.cache.items(), key=lambda item: item[1][2]  # Sort by timestamp
        )

        bytes_freed = 0
        for key, (_, source, _) in sorted_entries:
            # Remove entry
            del self.cache[key]
            entry_size = len(source)
            bytes_freed += entry_size
            self.current_size_bytes -= entry_size

            # Stop once we've freed enough space
            if bytes_freed >= required_bytes:
                break

        # If cache is still too full, remove one more entry
        if (
            self.current_size_bytes + required_bytes > self.max_size_mb * 1024 * 1024
            and self.cache
        ):
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][2])
            _, source, _ = self.cache[oldest_key]
            self.current_size_bytes -= len(source)
            del self.cache[oldest_key]

    def invalidate(self, file_path: Optional[Path] = None) -> None:
        """
        Invalidate cache entries.

        Args:
            file_path: If provided, invalidate only entries for this file.
                      If None, invalidate the entire cache.
        """
        with self.lock:
            if file_path is None:
                # Clear entire cache
                self.cache.clear()
                self.current_size_bytes = 0
            else:
                # Clear only entries for this file
                keys_to_remove = [key for key in self.cache if str(file_path) in key]
                for key in keys_to_remove:
                    _, source, _ = self.cache[key]
                    self.current_size_bytes -= len(source)
                    del self.cache[key]


# Global cache instance
tree_cache = TreeCache()


@lru_cache(maxsize=32)
def get_cached_parser(language: Any) -> TSParser:
    """Get a cached parser for a language."""
    parser = TSParser()
    parser.set_language(language)
    return parser
