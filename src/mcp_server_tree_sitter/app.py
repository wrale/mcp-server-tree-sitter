"""Shared application state (singletons) for the MCP Tree-sitter server.

Single place that holds config, project registry, language registry, and tree cache.
Uses __new__-based singletons; call get_app() to get the one instance.
"""

import threading
from typing import Optional

from .bootstrap import get_logger
from .cache.parser_cache import TreeCache
from .config import ConfigurationManager, ServerConfig
from .language.registry import LanguageRegistry
from .models.project import ProjectRegistry

logger = get_logger(__name__)


class App:
    """Process-wide shared state. One instance per process (__new__ singleton, thread-safe)."""

    _instance: Optional["App"] = None
    _lock = threading.RLock()

    def __new__(cls) -> "App":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        if getattr(self, "_initializing", False):
            return
        self._initializing = True
        logger.debug("Initializing app")

        self.config_manager = ConfigurationManager()
        config = self.config_manager.get_config()
        self.project_registry = ProjectRegistry()

        from .bootstrap import update_log_levels
        from .language.loader import load_all_language_data

        load_all_language_data()
        self.language_registry = LanguageRegistry(
            preferred_languages=config.language.preferred_languages,
        )
        self.tree_cache = TreeCache(
            max_size_mb=config.cache.max_size_mb,
            ttl_seconds=config.cache.ttl_seconds,
            enabled=config.cache.enabled,
        )

        def _on_config_loaded(loaded_config: ServerConfig) -> None:
            self.tree_cache.set_enabled(loaded_config.cache.enabled)
            self.tree_cache.set_max_size_mb(loaded_config.cache.max_size_mb)
            self.tree_cache.set_ttl_seconds(loaded_config.cache.ttl_seconds)
            update_log_levels(loaded_config.log_level)

        self.config_manager.set_on_config_loaded(_on_config_loaded)

        self._initializing = False
        self._initialized = True

    def get_config(self) -> ServerConfig:
        return self.config_manager.get_config()


def get_app() -> App:
    """Return the single App instance (same every time)."""
    return App()
