"""Configuration management for mcp-server-tree-sitter."""

import os
from pathlib import Path
from typing import Optional

import yaml  # type: ignore
from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Configuration for caching behavior."""

    enabled: bool = True
    max_size_mb: int = 100
    ttl_seconds: int = 300  # Time-to-live for cached items


class SecurityConfig(BaseModel):
    """Security settings."""

    max_file_size_mb: int = 5
    excluded_dirs: list[str] = Field(default_factory=lambda: [".git", "node_modules", "__pycache__"])
    allowed_extensions: Optional[list[str]] = None  # None means all extensions allowed


class LanguageConfig(BaseModel):
    """Language-specific configuration."""

    auto_install: bool = False  # DEPRECATED: No longer used with tree-sitter-language-pack
    default_max_depth: int = 5  # Default depth for AST traversal
    preferred_languages: list[str] = Field(default_factory=list)


class ServerConfig(BaseModel):
    """Main server configuration."""

    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    language: LanguageConfig = Field(default_factory=LanguageConfig)
    log_level: str = "INFO"
    max_results_default: int = 100

    @classmethod
    def from_file(cls, path: str) -> "ServerConfig":
        """Load configuration from YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            return cls()

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        config = cls()

        # Example of loading from env vars
        if os.environ.get("MCP_TS_CACHE_ENABLED"):
            cache_enabled = os.environ.get("MCP_TS_CACHE_ENABLED")
            if cache_enabled is not None:
                config.cache.enabled = cache_enabled.lower() == "true"

        if os.environ.get("MCP_TS_CACHE_MAX_SIZE_MB"):
            max_size = os.environ.get("MCP_TS_CACHE_MAX_SIZE_MB")
            if max_size is not None:
                config.cache.max_size_mb = int(max_size)

        if os.environ.get("MCP_TS_CACHE_TTL_SECONDS"):
            ttl = os.environ.get("MCP_TS_CACHE_TTL_SECONDS")
            if ttl is not None:
                config.cache.ttl_seconds = int(ttl)

        if os.environ.get("MCP_TS_SECURITY_MAX_FILE_SIZE_MB"):
            max_file_size = os.environ.get("MCP_TS_SECURITY_MAX_FILE_SIZE_MB")
            if max_file_size is not None:
                config.security.max_file_size_mb = int(max_file_size)

        if os.environ.get("MCP_TS_LANGUAGE_AUTO_INSTALL"):
            auto_install = os.environ.get("MCP_TS_LANGUAGE_AUTO_INSTALL")
            if auto_install is not None:
                config.language.auto_install = auto_install.lower() == "true"

        if os.environ.get("MCP_TS_LANGUAGE_DEFAULT_MAX_DEPTH"):
            default_max_depth = os.environ.get("MCP_TS_LANGUAGE_DEFAULT_MAX_DEPTH")
            if default_max_depth is not None:
                config.language.default_max_depth = int(default_max_depth)

        if os.environ.get("MCP_TS_LOG_LEVEL"):
            log_level = os.environ.get("MCP_TS_LOG_LEVEL")
            if log_level is not None:
                config.log_level = log_level

        return config


# Global config instance
CONFIG = ServerConfig()


def load_config(config_path: Optional[str] = None) -> None:
    """Load and initialize configuration.

    Args:
        config_path: Path to YAML config file
    """
    global CONFIG

    if config_path:
        CONFIG = ServerConfig.from_file(config_path)
    elif os.environ.get("MCP_TS_CONFIG_PATH"):
        config_path_env = os.environ.get("MCP_TS_CONFIG_PATH")
        if config_path_env is not None:
            CONFIG = ServerConfig.from_file(config_path_env)
    else:
        # Load from env vars
        CONFIG = ServerConfig.from_env()
