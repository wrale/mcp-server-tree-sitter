"""Configuration schema and public API for MCP Tree-sitter.

Precedence: environment variables > explicit updates > YAML file > defaults.
Import from this module for backward compatibility; schema lives in config_schema.
"""

from .config_env import update_config_from_env
from .config_loader import (
    ConfigurationManager,
    get_default_config_path,
    load_config,
    update_config_from_new,
)
from .config_schema import (
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
    "ConfigurationManager",
    "LanguageConfig",
    "SecurityConfig",
    "ServerConfig",
    "get_default_config_path",
    "load_config",
    "update_config_from_env",
    "update_config_from_new",
]
