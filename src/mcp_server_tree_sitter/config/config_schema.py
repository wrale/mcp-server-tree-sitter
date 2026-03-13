"""Configuration schema and types for MCP Tree-sitter.

Precedence: environment variables > explicit updates > YAML file > defaults.
Env format: MCP_TS_SECTION_SETTING (e.g. MCP_TS_CACHE_MAX_SIZE_MB) or MCP_TS_SETTING.

Default values and validation are defined here once; used by the schema and by
configure-tool fallbacks when invalid values are supplied.
"""

from typing import TypeAlias

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

ConfigValue: TypeAlias = int | float | bool | str | None | list[str]

# Single source of truth for these defaults (schema and invalid-value fallback).
DEFAULT_LOG_LEVEL: str = "INFO"
DEFAULT_MAX_FILE_SIZE_MB: int = 5
VALID_LOG_LEVELS: tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR")


class _CacheDict(TypedDict):
    enabled: bool
    max_size_mb: int
    ttl_seconds: int


class _SecurityDict(TypedDict):
    max_file_size_mb: int
    excluded_dirs: list[str]


class _LanguageDict(TypedDict):
    default_max_depth: int


class ConfigDict(TypedDict):
    """Serialized config shape returned by ConfigurationManager.to_dict()."""

    cache: _CacheDict
    security: _SecurityDict
    language: _LanguageDict
    log_level: str


class CacheConfig(BaseModel):
    """Configuration for caching behavior."""

    enabled: bool = True
    max_size_mb: int = 100
    ttl_seconds: int = 300


class SecurityConfig(BaseModel):
    """Security settings."""

    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    excluded_dirs: list[str] = Field(default_factory=lambda: [".git", "node_modules", "__pycache__"])
    allowed_extensions: list[str] | None = None


class LanguageConfig(BaseModel):
    """Language-specific configuration."""

    default_max_depth: int = 5
    preferred_languages: list[str] = Field(default_factory=list)


class ServerConfig(BaseModel):
    """Main server configuration."""

    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    language: LanguageConfig = Field(default_factory=LanguageConfig)
    log_level: str = DEFAULT_LOG_LEVEL
    max_results_default: int = 100

    @classmethod
    def from_file(cls, path: str) -> "ServerConfig":
        """Load configuration from a YAML file (with env overrides applied)."""
        from .config_loader import load_config_from_file

        return load_config_from_file(path)

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables only."""
        from .config_env import update_config_from_env

        config = cls()
        update_config_from_env(config)
        return config
