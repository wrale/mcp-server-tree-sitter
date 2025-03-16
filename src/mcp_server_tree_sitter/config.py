"""Configuration management for mcp-server-tree-sitter."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Configuration for caching behavior."""

    enabled: bool = True
    max_size_mb: int = 100
    ttl_seconds: int = 300  # Time-to-live for cached items


class SecurityConfig(BaseModel):
    """Security settings."""

    max_file_size_mb: int = 5
    excluded_dirs: list[str] = Field(
        default_factory=lambda: [".git", "node_modules", "__pycache__"]
    )
    allowed_extensions: Optional[list[str]] = None  # None means all extensions allowed


class LanguageConfig(BaseModel):
    """Language-specific configuration."""

    auto_install: bool = False  # Whether to auto-install missing parsers
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
            config.cache.enabled = (
                os.environ.get("MCP_TS_CACHE_ENABLED").lower() == "true"
            )

        if os.environ.get("MCP_TS_CACHE_MAX_SIZE_MB"):
            config.cache.max_size_mb = int(os.environ.get("MCP_TS_CACHE_MAX_SIZE_MB"))

        if os.environ.get("MCP_TS_CACHE_TTL_SECONDS"):
            config.cache.ttl_seconds = int(os.environ.get("MCP_TS_CACHE_TTL_SECONDS"))

        if os.environ.get("MCP_TS_SECURITY_MAX_FILE_SIZE_MB"):
            config.security.max_file_size_mb = int(
                os.environ.get("MCP_TS_SECURITY_MAX_FILE_SIZE_MB")
            )

        if os.environ.get("MCP_TS_LANGUAGE_AUTO_INSTALL"):
            config.language.auto_install = (
                os.environ.get("MCP_TS_LANGUAGE_AUTO_INSTALL").lower() == "true"
            )

        if os.environ.get("MCP_TS_LANGUAGE_DEFAULT_MAX_DEPTH"):
            config.language.default_max_depth = int(
                os.environ.get("MCP_TS_LANGUAGE_DEFAULT_MAX_DEPTH")
            )

        if os.environ.get("MCP_TS_LOG_LEVEL"):
            config.log_level = os.environ.get("MCP_TS_LOG_LEVEL")

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
        CONFIG = ServerConfig.from_file(os.environ.get("MCP_TS_CONFIG_PATH"))
    else:
        # Load from env vars
        CONFIG = ServerConfig.from_env()
