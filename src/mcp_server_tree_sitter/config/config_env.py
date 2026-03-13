"""Environment variable parsing for MCP Tree-sitter configuration.

Environment variables use the format:
- MCP_TS_SECTION_SETTING - For section settings (e.g., MCP_TS_CACHE_MAX_SIZE_MB)
- MCP_TS_SETTING - For top-level settings (e.g., MCP_TS_LOG_LEVEL)
"""

import logging
import os

from .config_schema import ConfigValue, ServerConfig

logger = logging.getLogger(__name__)


def update_config_from_env(config: ServerConfig) -> None:
    """Update configuration from environment variables.

    Applies all environment variables with the MCP_TS_ prefix to the provided
    config object, using the single underscore format only.

    Args:
        config: The ServerConfig object to update with environment variables.
    """
    env_prefix = "MCP_TS_"
    env_vars = {k: v for k, v in os.environ.items() if k.startswith(env_prefix)}

    for env_name, env_value in env_vars.items():
        key = env_name[len(env_prefix) :]
        logger.debug(f"Processing environment variable: {env_name}, key after prefix removal: {key}")

        parts = key.lower().split("_")

        if len(parts) > 1 and hasattr(config, parts[0]):
            section = parts[0]
            setting = "_".join(parts[1:])
            logger.debug(f"Single underscore format: section={section}, setting={setting}")
        else:
            section = None
            setting = key.lower()
            logger.debug(f"Top-level setting: {setting}")

        if section is None:
            if hasattr(config, setting):
                orig_value = getattr(config, setting)
                new_value = _convert_value(env_value, orig_value)
                setattr(config, setting, new_value)
                logger.debug(f"Applied {env_name} to {setting}: {orig_value} -> {new_value}")
            else:
                logger.warning(f"Unknown top-level setting in environment variable {env_name}: {setting}")
        elif hasattr(config, section):
            section_obj = getattr(config, section)
            if hasattr(section_obj, setting):
                orig_value = getattr(section_obj, setting)
                new_value = _convert_value(env_value, orig_value)
                setattr(section_obj, setting, new_value)
                logger.debug(f"Applied {env_name} to {section}.{setting}: {orig_value} -> {new_value}")
            else:
                logger.warning(f"Unknown setting {setting} in section {section} from {env_name}")


def _convert_value(value_str: str, current_value: ConfigValue) -> ConfigValue:
    """Convert string from environment to the appropriate type.

    Args:
        value_str: The string value from the environment variable.
        current_value: The current value used to determine the type.

    Returns:
        The converted value, or the original value if conversion fails.
    """
    try:
        if isinstance(current_value, bool):
            return value_str.lower() in ("true", "yes", "1", "y", "t", "on")
        if isinstance(current_value, int):
            return int(value_str)
        if isinstance(current_value, float):
            return float(value_str)
        if isinstance(current_value, list):
            return [item.strip() for item in value_str.split(",")]
        return value_str
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Failed to convert value '{value_str}' to type {type(current_value).__name__}: {e}"
        )
        return current_value
