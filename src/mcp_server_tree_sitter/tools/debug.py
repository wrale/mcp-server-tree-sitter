"""Debug tools for diagnosing configuration issues."""

from pathlib import Path
from typing import Any, Dict

import yaml

from ..config import ServerConfig, update_config_from_new
from ..context import global_context


def diagnose_yaml_config(config_path: str) -> Dict[str, Any]:
    """Diagnose issues with YAML configuration loading.

    Args:
        config_path: Path to YAML config file

    Returns:
        Dictionary with diagnostic information
    """
    result = {
        "file_path": config_path,
        "exists": False,
        "readable": False,
        "yaml_valid": False,
        "parsed_data": None,
        "config_before": None,
        "config_after": None,
        "error": None,
    }

    # Check if file exists
    path_obj = Path(config_path)
    result["exists"] = path_obj.exists()

    if not result["exists"]:
        result["error"] = f"File does not exist: {config_path}"
        return result

    # Check if file is readable
    try:
        with open(path_obj, "r") as f:
            content = f.read()
            result["readable"] = True
            result["file_content"] = content
    except Exception as e:
        result["error"] = f"Error reading file: {str(e)}"
        return result

    # Try to parse YAML
    try:
        config_data = yaml.safe_load(content)
        result["yaml_valid"] = True
        result["parsed_data"] = config_data
    except Exception as e:
        result["error"] = f"Error parsing YAML: {str(e)}"
        return result

    # Check if parsed data is None or empty
    if config_data is None:
        result["error"] = "YAML parser returned None (file empty or contains only comments)"
        return result

    if not isinstance(config_data, dict):
        result["error"] = f"YAML parser returned non-dict: {type(config_data)}"
        return result

    # Try creating a new config
    try:
        # Get current config
        current_config = global_context.get_config()
        result["config_before"] = {
            "cache.max_size_mb": current_config.cache.max_size_mb,
            "security.max_file_size_mb": current_config.security.max_file_size_mb,
            "language.default_max_depth": current_config.language.default_max_depth,
        }

        # Create new config from parsed data
        new_config = ServerConfig(**config_data)

        # Before update
        result["new_config"] = {
            "cache.max_size_mb": new_config.cache.max_size_mb,
            "security.max_file_size_mb": new_config.security.max_file_size_mb,
            "language.default_max_depth": new_config.language.default_max_depth,
        }

        # Update config
        update_config_from_new(current_config, new_config)

        # After update
        result["config_after"] = {
            "cache.max_size_mb": current_config.cache.max_size_mb,
            "security.max_file_size_mb": current_config.security.max_file_size_mb,
            "language.default_max_depth": current_config.language.default_max_depth,
        }

    except Exception as e:
        result["error"] = f"Error updating config: {str(e)}"
        return result

    return result
