"""Configuration schema and public API for MCP Tree-sitter.

Configuration precedence (highest to lowest):
  1. Explicit updates via update_value() — runtime changes take effect immediately
     and are not overwritten by env or file.
  2. Environment variables (MCP_TS_*) — applied exactly once at load time
     (when config is created or when a file is loaded).
  3. YAML file — values from the config file when present.
  4. Defaults — ServerConfig / schema defaults.

Import from this package for configuration types and loading.
"""

from .config_env import update_config_from_env
from .config_loader import (
    ConfigurationManager,
    get_default_config_path,
    load_config,
    load_config_from_file,
    update_config_from_new,
)
from .config_schema import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_FILE_SIZE_MB,
    VALID_LOG_LEVELS,
    CacheConfig,
    ConfigDict,
    ConfigValue,
    LanguageConfig,
    SecurityConfig,
    ServerConfig,
)

__all__ = [
    "CacheConfig",
    "ConfigDict",
    "ConfigValue",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_MAX_FILE_SIZE_MB",
    "ConfigurationManager",
    "LanguageConfig",
    "SecurityConfig",
    "ServerConfig",
    "VALID_LOG_LEVELS",
    "get_default_config_path",
    "load_config",
    "load_config_from_file",
    "update_config_from_env",
    "update_config_from_new",
]
