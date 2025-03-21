"""Caching system for tree-sitter parse trees."""

import logging
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Import global_context at runtime to avoid circular imports
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
        """Initialize the tree cache with explicit size and TTL settings."""
        self.cache: Dict[str, Tuple[Any, bytes, float]] = {}  # (tree, source, timestamp)
        self.lock = threading.RLock()
        self.current_size_bytes = 0
        self.modified_trees: Dict[str, bool] = {}
        self.max_size_mb = max_size_mb or 100
        self.ttl_seconds = ttl_seconds or 300
        self.enabled = True

    def _get_cache_key(self, file_path: Path, language: str) -> str:
        """Generate cache key from file path and language."""
        return f"{language}:{str(file_path)}:{file_path.stat().st_mtime}"

    def set_enabled(self, enabled: bool) -> None:
        """Set whether caching is enabled."""
        self.enabled = enabled

    def set_max_size_mb(self, max_size_mb: int) -> None:
        """Set maximum cache size in MB."""
        self.max_size_mb = max_size_mb

    def set_ttl_seconds(self, ttl_seconds: int) -> None:
        """Set TTL for cache entries in seconds."""
        self.ttl_seconds = ttl_seconds

    def _get_max_size_mb(self) -> float:
        """Get current max size setting."""
        # Always get the latest from container config
        try:
            from ..di import get_container

            config = get_container().get_config()
            return config.cache.max_size_mb if self.enabled else 0  # Return 0 if disabled
        except (ImportError, AttributeError):
            # Fallback to instance value if container unavailable
            return self.max_size_mb

    def _get_ttl_seconds(self) -> int:
        """Get current TTL setting."""
        # Always get the latest from container config
        try:
            from ..di import get_container

            config = get_container().get_config()
            return config.cache.ttl_seconds
        except (ImportError, AttributeError):
            # Fallback to instance value if container unavailable
            return self.ttl_seconds

    def _is_cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        # Honor both local setting and container config
        try:
            from ..di import get_container

            config = get_container().get_config()
            is_enabled = self.enabled and config.cache.enabled
            # For very small caches, log the state
            if not is_enabled:
                logger.debug(
                    f"Cache disabled: self.enabled={self.enabled}, config.cache.enabled={config.cache.enabled}"
                )
            return is_enabled
        except (ImportError, AttributeError):
            # Fallback to instance value if container unavailable
            return self.enabled

    def get(self, file_path: Path, language: str) -> Optional[Tuple[Tree, bytes]]:
        """
        Get cached tree if available and not expired.

        Args:
            file_path: Path to the source file
            language: Language identifier

        Returns:
            Tuple of (tree, source_bytes) if cached, None otherwise
        """
        # Check if caching is enabled
        if not self._is_cache_enabled():
            return None

        try:
            cache_key = self._get_cache_key(file_path, language)
        except (FileNotFoundError, OSError):
            return None

        with self.lock:
            if cache_key in self.cache:
                tree, source, timestamp = self.cache[cache_key]

                # Check if cache entry has expired (using current config TTL)
                ttl_seconds = self._get_ttl_seconds()
                current_time = time.time()
                entry_age = current_time - timestamp
                if entry_age > ttl_seconds:
                    logger.debug(f"Cache entry expired: age={entry_age:.2f}s, ttl={ttl_seconds}s")
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
        # Check if caching is enabled
        is_enabled = self._is_cache_enabled()
        if not is_enabled:
            logger.debug(f"Skipping cache for {file_path}: caching is disabled")
            return

        try:
            cache_key = self._get_cache_key(file_path, language)
        except (FileNotFoundError, OSError):
            return

        source_size = len(source)

        # Check if adding this entry would exceed cache size limit (using current max size)
        max_size_mb = self._get_max_size_mb()
        max_size_bytes = max_size_mb * 1024 * 1024

        # If max_size is 0 or very small, disable caching
        if max_size_bytes <= 1024:  # If less than 1KB, don't cache
            logger.debug(f"Cache size too small: {max_size_mb}MB, skipping cache")
            return

        if source_size > max_size_bytes:
            logger.warning(f"File too large to cache: {file_path} ({source_size / (1024 * 1024):.2f}MB)")
            return

        with self.lock:
            # If entry already exists, subtract its size
            if cache_key in self.cache:
                _, old_source, _ = self.cache[cache_key]
                self.current_size_bytes -= len(old_source)
            else:
                # If we need to make room for a new entry, remove oldest entries
                if self.current_size_bytes + source_size > max_size_bytes:
                    self._evict_entries(source_size)

            # Store the new entry
            self.cache[cache_key] = (tree, source, time.time())
            self.current_size_bytes += source_size
            logger.debug(
                f"Added entry to cache: {file_path}, size: {source_size / 1024:.1f}KB, "
                f"total cache: {self.current_size_bytes / (1024 * 1024):.2f}MB"
            )

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
        # Get current max size from config
        max_size_mb = self._get_max_size_mb()
        max_size_bytes = max_size_mb * 1024 * 1024

        # Check if we actually need to evict anything
        if self.current_size_bytes + required_bytes <= max_size_bytes:
            return

        # If cache is empty (happens in tests sometimes), nothing to evict
        if not self.cache:
            return

        # Sort by timestamp (oldest first)
        sorted_entries = sorted(self.cache.items(), key=lambda item: item[1][2])

        bytes_freed = 0
        entries_removed = 0

        # Force removal of at least one entry in tests with very small caches (< 0.1MB)
        force_removal = max_size_mb < 0.1
        target_to_free = required_bytes

        # If cache is small, make sure we remove at least one item
        min_entries_to_remove = 1

        # If cache is very small, removing any entry should be enough
        if force_removal or max_size_bytes < 10 * 1024:  # Less than 10KB
            # For tests with very small caches, we need to be more aggressive
            target_to_free = self.current_size_bytes // 2  # Remove half the cache
            min_entries_to_remove = max(1, len(self.cache) // 2)
            logger.debug(f"Small cache detected ({max_size_mb}MB), removing {min_entries_to_remove} entries")

        # If cache is already too full, free more space to prevent continuous evictions
        elif self.current_size_bytes > max_size_bytes * 0.9:
            target_to_free += int(max_size_bytes * 0.2)  # Free extra 20%
            min_entries_to_remove = max(1, len(self.cache) // 4)

        for key, (_, source, _) in sorted_entries:
            # Remove entry
            del self.cache[key]
            if key in self.modified_trees:
                del self.modified_trees[key]

            entry_size = len(source)
            bytes_freed += entry_size
            self.current_size_bytes -= entry_size
            entries_removed += 1

            # Stop once we've freed enough space AND removed minimum entries
            if bytes_freed >= target_to_free and entries_removed >= min_entries_to_remove:
                break

        # Log the eviction with appropriate level
        log_msg = (
            f"Evicted {entries_removed} cache entries, freed {bytes_freed / 1024:.1f}KB, "
            f"current size: {self.current_size_bytes / (1024 * 1024):.2f}MB"
        )
        if force_removal:
            logger.debug(log_msg)
        else:
            logger.info(log_msg)

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


# The TreeCache is now initialized and managed by the DependencyContainer in di.py
# No global instance is needed here anymore.


# The following function is maintained for backward compatibility
def get_tree_cache() -> TreeCache:
    """Get the tree cache from the dependency container."""
    from ..di import get_container

    tree_cache = get_container().tree_cache
    return tree_cache


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
