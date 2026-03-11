"""YAML configuration loading and ConfigurationManager for MCP Tree-sitter."""

import logging
import os
from pathlib import Path
from typing import Optional, Union

import yaml

from .bootstrap import update_log_levels
from .config_env import update_config_from_env
from .config_schema import ConfigDict, ConfigValue, ServerConfig

logger = logging.getLogger(__name__)


def get_default_config_path() -> Optional[Path]:
    """Return the default configuration file path based on the platform."""
    import platform

    if platform.system() == "Windows":
        config_dir = Path(os.environ.get("USERPROFILE", "")) / ".config" / "tree-sitter"
    else:
        config_dir = Path(os.environ.get("HOME", "")) / ".config" / "tree-sitter"

    config_path = config_dir / "config.yaml"
    return config_path if config_path.exists() else None


def load_config_from_file(path: str) -> ServerConfig:
    """Load configuration from a YAML file and apply environment overrides."""
    config_path = Path(path)
    if not config_path.exists():
        logger.warning(f"Config file does not exist: {path}")
        return ServerConfig()

    try:
        with open(config_path, "r") as f:
            file_content = f.read()
            logger.debug(f"YAML File content:\n{file_content}")
        config_data = yaml.safe_load(file_content)
        logger.debug(f"Loaded config data: {config_data}")

        if config_data is None:
            logger.warning(f"Config file is empty or contains only comments: {path}")
            return ServerConfig()

        config = ServerConfig(**config_data)
        update_config_from_env(config)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration from {path}: {e}")
        logger.debug(__import__("traceback").format_exc())
        return ServerConfig()


def update_config_from_new(original: ServerConfig, new: ServerConfig) -> None:
    """Update the original config with values from the new config."""
    try:
        original.cache.enabled = new.cache.enabled
        original.cache.max_size_mb = new.cache.max_size_mb
        original.cache.ttl_seconds = new.cache.ttl_seconds
        original.security.max_file_size_mb = new.security.max_file_size_mb
        original.security.excluded_dirs = new.security.excluded_dirs.copy()
        original.security.allowed_extensions = (
            new.security.allowed_extensions.copy() if new.security.allowed_extensions else None
        )
        original.language.auto_install = new.language.auto_install
        original.language.default_max_depth = new.language.default_max_depth
        original.language.preferred_languages = new.language.preferred_languages.copy()
        original.log_level = new.log_level
        original.max_results_default = new.max_results_default
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        try:
            original.cache.max_size_mb = new.cache.max_size_mb
            original.security.max_file_size_mb = new.security.max_file_size_mb
            original.language.default_max_depth = new.language.default_max_depth
        except Exception as e2:
            logger.error(f"Fallback update also failed: {e2}")


def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """Load and initialize configuration from file and environment.

    Precedence: env vars > explicit path > MCP_TS_CONFIG_PATH > default path.
    """
    config = ServerConfig()
    path_to_load = (
        Path(config_path)
        if config_path
        else Path(os.environ["MCP_TS_CONFIG_PATH"])
        if os.environ.get("MCP_TS_CONFIG_PATH")
        else get_default_config_path()
    )
    if path_to_load and path_to_load.exists():
        try:
            if path_to_load.read_text().strip():
                update_config_from_new(config, load_config_from_file(str(path_to_load)))
        except Exception as e:
            logger.error(f"Error loading configuration from {path_to_load}: {e}")
            logger.debug(__import__("traceback").format_exc())
    update_config_from_env(config)
    return config


class ConfigurationManager:
    """Manages server configuration without relying on global variables."""

    def __init__(self, initial_config: Optional[ServerConfig] = None) -> None:
        self._config = initial_config or ServerConfig()
        self._logger = logging.getLogger(__name__)
        update_config_from_env(self._config)

    def get_config(self) -> ServerConfig:
        """Return the current configuration."""
        return self._config

    def load_from_file(self, path: Union[str, Path]) -> ServerConfig:
        """Load configuration from a YAML file and apply env overrides."""
        config_path = Path(path)
        if not config_path.exists():
            self._logger.error(f"Config file does not exist: {path}")
            return self._config
        try:
            file_content = config_path.read_text()
            if not file_content.strip():
                self._logger.error(f"Config file is empty: {path}")
                return self._config
            config_data = yaml.safe_load(file_content)
            if config_data is None or not isinstance(config_data, dict):
                self._logger.error(f"Invalid YAML config: {path}")
                return self._config
            update_config_from_new(self._config, ServerConfig(**config_data))
            update_config_from_env(self._config)
            try:
                from .di import get_container

                c = get_container()
                c.tree_cache.set_enabled(self._config.cache.enabled)
                c.tree_cache.set_max_size_mb(self._config.cache.max_size_mb)
                c.tree_cache.set_ttl_seconds(self._config.cache.ttl_seconds)
                update_log_levels(self._config.log_level)
            except (ImportError, AttributeError) as e:
                self._logger.warning(f"Could not apply config to dependencies: {e}")
            return self._config
        except Exception as e:
            self._logger.error(f"Error loading configuration from {path}: {e}")
            self._logger.debug(__import__("traceback").format_exc())
            return self._config

    def update_value(self, path: str, value: ConfigValue) -> None:
        """Update a configuration value by dot-notation path (e.g. cache.max_size_mb)."""
        parts = path.split(".")
        if len(parts) == 2:
            section, key = parts
            if hasattr(self._config, section):
                section_obj = getattr(self._config, section)
                if hasattr(section_obj, key):
                    old_value = getattr(section_obj, key)
                    setattr(section_obj, key, value)
                    self._logger.debug(f"Updated {path} from {old_value} to {value}")
                else:
                    self._logger.warning(f"Unknown config key: {key} in section {section}")
            else:
                self._logger.warning(f"Unknown config section: {section}")
        else:
            if hasattr(self._config, path):
                old_value = getattr(self._config, path)
                setattr(self._config, path, value)
                self._logger.debug(f"Updated {path} from {old_value} to {value}")
                if path == "log_level" and isinstance(value, (str, int)):
                    update_log_levels(value)
            else:
                self._logger.warning(f"Unknown config path: {path}")

        update_config_from_env(self._config)

    def to_dict(self) -> ConfigDict:
        """Return configuration as a serialized dictionary."""
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
