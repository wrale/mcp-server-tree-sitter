"""Caching system for tree-sitter parse trees."""

import logging
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..config import CONFIG
from ..utils.tree_sitter_types import (
    Parser,
    Tree,
    ensure_language,
    ensure_parser,
    ensure_tree,
)

logger = logging.getLogger(__name__)


class TreeCache:
    """Cache for parsed syntax trees."""

    def __init__(self, max_size_mb: Optional[int] = None, ttl_seconds: Optional[int] = None):
        self.max_size_mb = max_size_mb or CONFIG.cache.max_size_mb
        self.ttl_seconds = ttl_seconds or CONFIG.cache.ttl_seconds
        self.cache: Dict[str, Tuple[Any, bytes, float]] = {}  # (tree, source, timestamp)
        self.lock = threading.RLock()
        self.current_size_bytes = 0
        # Track modified trees for incremental parsing
        self.modified_trees: Dict[str, bool] = {}

    def _get_cache_key(self, file_path: Path, language: str) -> str:
        """Generate cache key from file path and language."""
        return f"{language}:{str(file_path)}:{file_path.stat().st_mtime}"

    def get(self, file_path: Path, language: str) -> Optional[Tuple[Tree, bytes]]:
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
                    if cache_key in self.modified_trees:
                        del self.modified_trees[cache_key]
                    return None

                # Cast to the correct type for type checking
                safe_tree = ensure_tree(tree)
                return safe_tree, source

        return None

    def put(self, file_path: Path, language: str, tree: Tree, source: bytes) -> None:
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
            logger.warning(f"File too large to cache: {file_path} ({source_size / (1024 * 1024):.2f}MB)")
            return

        with self.lock:
            # If entry already exists, subtract its size
            if cache_key in self.cache:
                _, old_source, _ = self.cache[cache_key]
                self.current_size_bytes -= len(old_source)
            else:
                # If we need to make room for a new entry, remove oldest entries
                if self.current_size_bytes + source_size > self.max_size_mb * 1024 * 1024:
                    self._evict_entries(source_size)

            # Store the new entry
            self.cache[cache_key] = (tree, source, time.time())
            self.current_size_bytes += source_size

            # Mark as not modified (fresh parse)
            self.modified_trees[cache_key] = False

    def mark_modified(self, file_path: Path, language: str) -> None:
        """
        Mark a tree as modified for tracking changes.

        Args:
            file_path: Path to the source file
            language: Language identifier
        """
        try:
            cache_key = self._get_cache_key(file_path, language)
            with self.lock:
                if cache_key in self.cache:
                    self.modified_trees[cache_key] = True
        except (FileNotFoundError, OSError):
            pass

    def is_modified(self, file_path: Path, language: str) -> bool:
        """
        Check if a tree has been modified since last parse.

        Args:
            file_path: Path to the source file
            language: Language identifier

        Returns:
            True if the tree has been modified, False otherwise
        """
        try:
            cache_key = self._get_cache_key(file_path, language)
            with self.lock:
                return self.modified_trees.get(cache_key, False)
        except (FileNotFoundError, OSError):
            return False

    def update_tree(self, file_path: Path, language: str, tree: Tree, source: bytes) -> None:
        """
        Update a cached tree after modification.

        Args:
            file_path: Path to the source file
            language: Language identifier
            tree: Updated parsed tree
            source: Updated source bytes
        """
        try:
            cache_key = self._get_cache_key(file_path, language)
        except (FileNotFoundError, OSError):
            return

        with self.lock:
            if cache_key in self.cache:
                _, old_source, _ = self.cache[cache_key]
                # Update size tracking
                self.current_size_bytes -= len(old_source)
                self.current_size_bytes += len(source)
                # Update cache entry
                self.cache[cache_key] = (tree, source, time.time())
                # Reset modified flag
                self.modified_trees[cache_key] = False
            else:
                # If not already in cache, just add it
                self.put(file_path, language, tree, source)

    def _evict_entries(self, required_bytes: int) -> None:
        """
        Evict entries to make room for new data.

        Args:
            required_bytes: Number of bytes to make room for
        """
        # Sort by timestamp (oldest first)
        sorted_entries = sorted(self.cache.items(), key=lambda item: item[1][2])  # Sort by timestamp

        bytes_freed = 0
        for key, (_, source, _) in sorted_entries:
            # Remove entry
            del self.cache[key]
            if key in self.modified_trees:
                del self.modified_trees[key]
            entry_size = len(source)
            bytes_freed += entry_size
            self.current_size_bytes -= entry_size

            # Stop once we've freed enough space
            if bytes_freed >= required_bytes:
                break

        # If cache is still too full, remove one more entry
        if self.current_size_bytes + required_bytes > self.max_size_mb * 1024 * 1024 and self.cache:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][2])
            _, source, _ = self.cache[oldest_key]
            self.current_size_bytes -= len(source)
            del self.cache[oldest_key]
            if oldest_key in self.modified_trees:
                del self.modified_trees[oldest_key]

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
                self.modified_trees.clear()
                self.current_size_bytes = 0
            else:
                # Clear only entries for this file
                keys_to_remove = [key for key in self.cache if str(file_path) in key]
                for key in keys_to_remove:
                    _, source, _ = self.cache[key]
                    self.current_size_bytes -= len(source)
                    del self.cache[key]
                    if key in self.modified_trees:
                        del self.modified_trees[key]


# Global cache instance
tree_cache = TreeCache()


@lru_cache(maxsize=32)
def get_cached_parser(language: Any) -> Parser:
    """Get a cached parser for a language."""
    parser = Parser()
    safe_language = ensure_language(language)

    # Try both set_language and language methods
    try:
        parser.set_language(safe_language)  # type: ignore
    except AttributeError:
        if hasattr(parser, "language"):
            # Use the language method if available
            parser.language = safe_language  # type: ignore
        else:
            # Fallback to setting the attribute directly
            parser.language = safe_language  # type: ignore

    return ensure_parser(parser)
