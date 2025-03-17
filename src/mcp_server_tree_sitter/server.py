"""MCP server implementation for Tree-sitter with dependency injection."""

import logging
import os
from typing import Any, Dict, Optional, Tuple

from mcp.server.fastmcp import FastMCP

from .config import ServerConfig
from .di import DependencyContainer, get_container

# Create server instance
mcp = FastMCP("tree_sitter")

# Set up logger
logger = logging.getLogger(__name__)


def configure_with_context(
    container: DependencyContainer,
    config_path: Optional[str] = None,
    cache_enabled: Optional[bool] = None,
    max_file_size_mb: Optional[int] = None,
    log_level: Optional[str] = None,
) -> Tuple[Dict[str, Any], ServerConfig]:
    """Configure the server with explicit context.

    Args:
        container: DependencyContainer instance
        config_path: Path to YAML config file
        cache_enabled: Whether to enable parse tree caching
        max_file_size_mb: Maximum file size in MB
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Tuple of (configuration dict, ServerConfig object)
    """
    # Get initial config for comparison
    config_manager = container.config_manager
    tree_cache = container.tree_cache
    initial_config = config_manager.get_config()
    logger.info(
        f"Initial configuration: "
        f"cache.max_size_mb = {initial_config.cache.max_size_mb}, "
        f"security.max_file_size_mb = {initial_config.security.max_file_size_mb}, "
        f"language.default_max_depth = {initial_config.language.default_max_depth}"
    )

    # Load config if path provided
    if config_path:
        logger.info(f"Configuring server with YAML config from: {config_path}")
        # Log absolute path to ensure we're looking at the right file
        abs_path = os.path.abspath(config_path)
        logger.info(f"Absolute path: {abs_path}")

        # Check if the file exists before trying to load it
        if not os.path.exists(abs_path):
            logger.error(f"Config file does not exist: {abs_path}")

        config_manager.load_from_file(abs_path)

        # Log configuration after loading YAML
        intermediate_config = config_manager.get_config()
        logger.info(
            f"Configuration after loading YAML: "
            f"cache.max_size_mb = {intermediate_config.cache.max_size_mb}, "
            f"security.max_file_size_mb = {intermediate_config.security.max_file_size_mb}, "
            f"language.default_max_depth = {intermediate_config.language.default_max_depth}"
        )

    # Update specific settings if provided
    if cache_enabled is not None:
        logger.info(f"Setting cache.enabled to {cache_enabled}")
        config_manager.update_value("cache.enabled", cache_enabled)
        tree_cache.set_enabled(cache_enabled)

    if max_file_size_mb is not None:
        logger.info(f"Setting security.max_file_size_mb to {max_file_size_mb}")
        config_manager.update_value("security.max_file_size_mb", max_file_size_mb)

    if log_level is not None:
        logger.info(f"Setting log_level to {log_level}")
        config_manager.update_value("log_level", log_level)

        # Apply log level directly to loggers
        log_level_value = getattr(logging, log_level, None)
        if log_level_value is not None:
            # Apply to root logger - this should cascade to all child loggers unless they override it
            root_logger = logging.getLogger("mcp_server_tree_sitter")
            root_logger.setLevel(log_level_value)

            # Override on all existing loggers to ensure immediate propagation
            for name in logging.root.manager.loggerDict:
                if name == "mcp_server_tree_sitter" or name.startswith("mcp_server_tree_sitter."):
                    logging.getLogger(name).setLevel(log_level_value)

            logger.info(f"Applied log level {log_level} to mcp_server_tree_sitter loggers")

    # Get final configuration
    config = config_manager.get_config()
    logger.info(
        f"Final configuration: "
        f"cache.max_size_mb = {config.cache.max_size_mb}, "
        f"security.max_file_size_mb = {config.security.max_file_size_mb}, "
        f"language.default_max_depth = {config.language.default_max_depth}"
    )

    # Return current config as dict and the actual config object
    config_dict = config_manager.to_dict()
    return config_dict, config


def main() -> None:
    """Run the server"""
    # Get the container
    container = get_container()

    # Register capabilities and tools
    from .capabilities import register_capabilities
    from .tools.registration import register_tools

    register_capabilities(mcp)
    register_tools(mcp, container)

    # Load configuration from environment
    config = container.get_config()

    # Update tree cache settings from config
    container.tree_cache.set_max_size_mb(config.cache.max_size_mb)
    container.tree_cache.set_enabled(config.cache.enabled)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
