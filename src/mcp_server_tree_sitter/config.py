"""Configuration management with explicit manager class."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
    excluded_dirs: List[str] = Field(default_factory=lambda: [".git", "node_modules", "__pycache__"])
    allowed_extensions: Optional[List[str]] = None  # None means all extensions allowed


class LanguageConfig(BaseModel):
    """Language-specific configuration."""

    auto_install: bool = False  # DEPRECATED: No longer used with tree-sitter-language-pack
    default_max_depth: int = 5  # Default depth for AST traversal
    preferred_languages: List[str] = Field(default_factory=list)


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
        logger = logging.getLogger(__name__)
        config_path = Path(path)
        if not config_path.exists():
            logger.warning(f"Config file does not exist: {path}")
            return cls()

        try:
            with open(config_path, "r") as f:
                file_content = f.read()
                logger.debug(f"YAML File content:\n{file_content}")
                config_data = yaml.safe_load(file_content)

            logger.debug(f"Loaded config data: {config_data}")

            if config_data is None:
                logger.warning(f"Config file is empty or contains only comments: {path}")
                return cls()

            return cls(**config_data)
        except Exception as e:
            logger.error(f"Error loading configuration from {path}: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return cls()

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


class ConfigurationManager:
    """Manages server configuration without relying on global variables."""

    def __init__(self, initial_config: Optional[ServerConfig] = None):
        """Initialize with optional initial configuration."""
        self._config = initial_config or ServerConfig()
        self._logger = logging.getLogger(__name__)

    def get_config(self) -> ServerConfig:
        """Get the current configuration."""
        return self._config

    def load_from_file(self, path: Union[str, Path]) -> ServerConfig:
        """Load configuration from a YAML file."""
        self._logger.info(f"Loading configuration from file: {path}")
        config_path = Path(path)

        # Log more information for debugging
        self._logger.info(f"Absolute path: {config_path.absolute()}")
        self._logger.info(f"Path exists: {config_path.exists()}")

        if not config_path.exists():
            self._logger.error(f"Config file does not exist: {path}")
            return self._config

        try:
            with open(config_path, "r") as f:
                file_content = f.read()
                self._logger.info(f"YAML File content:\n{file_content}")
                # Check if file content is empty
                if not file_content.strip():
                    self._logger.error(f"Config file is empty: {path}")
                    return self._config

                # Try to parse YAML
                config_data = yaml.safe_load(file_content)
                self._logger.info(f"YAML parsing successful? {config_data is not None}")

            self._logger.info(f"Loaded config data: {config_data}")

            if config_data is None:
                self._logger.error(f"Config file is empty or contains only comments: {path}")
                return self._config

            # Debug output before update
            self._logger.info(
                f"Before update: cache.max_size_mb = {self._config.cache.max_size_mb}, "
                f"security.max_file_size_mb = {self._config.security.max_file_size_mb}"
            )

            # Better error handling for invalid YAML data
            if not isinstance(config_data, dict):
                self._logger.error(f"YAML data is not a dictionary: {type(config_data)}")
                return self._config

            # Log the YAML structure
            self._logger.info(f"YAML structure: {list(config_data.keys()) if config_data else 'None'}")

            # Create new config from file data
            try:
                new_config = ServerConfig(**config_data)

                # Debug output for new config
                self._logger.info(
                    f"New config: cache.max_size_mb = {new_config.cache.max_size_mb}, "
                    f"security.max_file_size_mb = {new_config.security.max_file_size_mb}"
                )
            except Exception as e:
                self._logger.error(f"Error creating ServerConfig from YAML data: {e}")
                return self._config

            # Instead of simply replacing config object, use update_config_from_new to ensure
            # all attributes are copied correctly (similar to how load_config function works)
            update_config_from_new(self._config, new_config)

            # Debug output after update
            self._logger.info(
                f"After update: cache.max_size_mb = {self._config.cache.max_size_mb}, "
                f"security.max_file_size_mb = {self._config.security.max_file_size_mb}"
            )

            # Apply configuration to dependencies
            try:
                from .di import get_container

                container = get_container()

                # Update tree cache settings
                self._logger.info(
                    f"Setting tree cache: enabled={self._config.cache.enabled}, "
                    f"size={self._config.cache.max_size_mb}MB, ttl={self._config.cache.ttl_seconds}s"
                )
                container.tree_cache.set_enabled(self._config.cache.enabled)
                container.tree_cache.set_max_size_mb(self._config.cache.max_size_mb)
                container.tree_cache.set_ttl_seconds(self._config.cache.ttl_seconds)

                # Update logging configuration
                log_level_value = getattr(logging, self._config.log_level, None)
                if log_level_value:
                    # Apply to root logger and all existing loggers
                    root_logger = logging.getLogger("mcp_server_tree_sitter")
                    root_logger.setLevel(log_level_value)

                    # Override on all existing loggers to ensure immediate propagation
                    for name in logging.root.manager.loggerDict:
                        if name == "mcp_server_tree_sitter" or name.startswith("mcp_server_tree_sitter."):
                            logging.getLogger(name).setLevel(log_level_value)

                    self._logger.info(
                        f"Applied log level {self._config.log_level} to all mcp_server_tree_sitter loggers"
                    )

                self._logger.info("Applied configuration to dependencies")
            except (ImportError, AttributeError) as e:
                self._logger.warning(f"Could not apply config to dependencies: {e}")

            self._logger.info(f"Successfully loaded configuration from {path}")

            return self._config

        except Exception as e:
            self._logger.error(f"Error loading configuration from {path}: {e}")
            import traceback

            self._logger.error(traceback.format_exc())
            return self._config

    def update_value(self, path: str, value: Any) -> None:
        """Update a specific configuration value by dot-notation path."""
        parts = path.split(".")

        # Handle two levels deep for now (e.g., "cache.max_size_mb")
        if len(parts) == 2:
            section, key = parts

            if hasattr(self._config, section):
                section_obj = getattr(self._config, section)
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)
                    self._logger.debug(f"Updated config value {path} to {value}")
                else:
                    self._logger.warning(f"Unknown config key: {key} in section {section}")
            else:
                self._logger.warning(f"Unknown config section: {section}")
        else:
            # Handle top-level attributes
            if hasattr(self._config, path):
                setattr(self._config, path, value)
                self._logger.debug(f"Updated config value {path} to {value}")

                # If updating log_level, apply it to the logger
                if path == "log_level":
                    log_level_value = getattr(logging, value, None)
                    if log_level_value:
                        # Apply to root logger and all existing loggers
                        root_logger = logging.getLogger("mcp_server_tree_sitter")
                        root_logger.setLevel(log_level_value)

                        # Override on all existing loggers to ensure immediate propagation
                        for name in logging.root.manager.loggerDict:
                            if name == "mcp_server_tree_sitter" or name.startswith("mcp_server_tree_sitter."):
                                logging.getLogger(name).setLevel(log_level_value)

                        self._logger.debug(f"Applied log level {value} to all mcp_server_tree_sitter loggers")
            else:
                self._logger.warning(f"Unknown config path: {path}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "cache": {
                "enabled": self._config.cache.enabled,
                "max_size_mb": self._config.cache.max_size_mb,
                "ttl_seconds": self._config.cache.ttl_seconds,
            },
            "security": {
                "max_file_size_mb": self._config.security.max_file_size_mb,
                "excluded_dirs": self._config.security.excluded_dirs,
            },
            "language": {
                "auto_install": self._config.language.auto_install,
                "default_max_depth": self._config.language.default_max_depth,
            },
            "log_level": self._config.log_level,
        }


# We've removed the global CONFIG instance to eliminate global state and
# potential concurrency issues. All code should now use either:
# 1. The context's config_manager.get_config() method
# 2. A locally instantiated ServerConfig object
# 3. Configuration passed as function parameters


def get_default_config_path() -> Optional[Path]:
    """Get the default configuration file path based on the platform."""
    import platform

    if platform.system() == "Windows":
        config_dir = Path(os.environ.get("USERPROFILE", "")) / ".config" / "tree-sitter"
    else:
        config_dir = Path(os.environ.get("HOME", "")) / ".config" / "tree-sitter"

    config_path = config_dir / "config.yaml"

    if config_path.exists():
        return config_path

    return None


def update_config_from_new(original: ServerConfig, new: ServerConfig) -> None:
    """Update the original config with values from the new config."""
    logger = logging.getLogger(__name__)

    # Log before values
    logger.info(
        f"[update_config_from_new] Before: cache.max_size_mb={original.cache.max_size_mb}, "
        f"security.max_file_size_mb={original.security.max_file_size_mb}"
    )
    logger.info(
        f"[update_config_from_new] New values: cache.max_size_mb={new.cache.max_size_mb}, "
        f"security.max_file_size_mb={new.security.max_file_size_mb}"
    )

    # Update all attributes, copying collections to avoid reference issues
    try:
        # Cache settings
        original.cache.enabled = new.cache.enabled
        original.cache.max_size_mb = new.cache.max_size_mb
        original.cache.ttl_seconds = new.cache.ttl_seconds

        # Security settings
        original.security.max_file_size_mb = new.security.max_file_size_mb
        original.security.excluded_dirs = new.security.excluded_dirs.copy()
        if new.security.allowed_extensions:
            original.security.allowed_extensions = new.security.allowed_extensions.copy()
        else:
            original.security.allowed_extensions = None

        # Language settings
        original.language.auto_install = new.language.auto_install
        original.language.default_max_depth = new.language.default_max_depth
        original.language.preferred_languages = new.language.preferred_languages.copy()

        # Other settings
        original.log_level = new.log_level
        original.max_results_default = new.max_results_default

        # Log after values to confirm update succeeded
        logger.info(
            f"[update_config_from_new] After: cache.max_size_mb={original.cache.max_size_mb}, "
            f"security.max_file_size_mb={original.security.max_file_size_mb}"
        )
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        # Ensure at least some values get updated
        try:
            original.cache.max_size_mb = new.cache.max_size_mb
            original.security.max_file_size_mb = new.security.max_file_size_mb
            original.language.default_max_depth = new.language.default_max_depth
            logger.info("Fallback update succeeded with basic values")
        except Exception as e2:
            logger.error(f"Fallback update also failed: {e2}")


def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """Load and initialize configuration.

    Args:
        config_path: Path to YAML config file

    Returns:
        ServerConfig: The loaded configuration
    """
    logger = logging.getLogger(__name__)
    logger.info(f"load_config called with config_path={config_path}")

    # Create a new config instance
    config = ServerConfig()

    # Determine which config path to use
    path_to_load = None

    if config_path:
        # Use explicitly provided path
        path_to_load = Path(config_path)
    elif os.environ.get("MCP_TS_CONFIG_PATH"):
        # Use path from environment variable
        config_path_env = os.environ.get("MCP_TS_CONFIG_PATH")
        if config_path_env is not None:
            path_to_load = Path(config_path_env)
    else:
        # Try to use default config path
        default_path = get_default_config_path()
        if default_path:
            path_to_load = default_path
            logger.info(f"Using default configuration from {path_to_load}")
        else:
            # No config file available, use environment variables
            logger.info("No configuration file found, using environment variables")
            env_config = ServerConfig.from_env()
            update_config_from_new(config, env_config)
            return config

    # Load configuration from the determined path
    if path_to_load:
        try:
            logger.info(f"Loading configuration from file: {path_to_load}")
            if not path_to_load.exists():
                logger.error(f"Config file does not exist: {path_to_load}")
                return config

            with open(path_to_load, "r") as f:
                content = f.read()
                logger.debug(f"File content:\n{content}")
                if not content.strip():
                    logger.warning("Config file is empty")
                    return config

            # Load new configuration
            logger.info(f"Loading configuration from {str(path_to_load)}")
            new_config = ServerConfig.from_file(str(path_to_load))

            # Debug output before update
            logger.info(
                f"New configuration loaded: cache.max_size_mb = {new_config.cache.max_size_mb}, "
                f"security.max_file_size_mb = {new_config.security.max_file_size_mb}"
            )

            # Update the config by copying all attributes
            update_config_from_new(config, new_config)

            # Debug output after update
            logger.info(f"Successfully loaded configuration from {path_to_load}")
            logger.debug(
                f"Updated config: cache.max_size_mb = {config.cache.max_size_mb}, "
                f"security.max_file_size_mb = {config.security.max_file_size_mb}"
            )

        except Exception as e:
            logger.error(f"Error loading configuration from {path_to_load}: {e}")
            import traceback

            logger.debug(traceback.format_exc())

    return config
