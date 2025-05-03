"""MCP server implementation for Tree-sitter with dependency injection."""

import os
from typing import Any, Dict, Optional, Tuple

from mcp.server.fastmcp import FastMCP

from .bootstrap import get_logger, update_log_levels
from .config import ServerConfig
from .di import DependencyContainer, get_container

# Create server instance
mcp = FastMCP("tree_sitter")

# Set up logger
logger = get_logger(__name__)


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

        # Apply log level using already imported update_log_levels
        update_log_levels(log_level)
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
    """Run the server with command-line argument handling"""
    import argparse
    import sys

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Tree-sitter Server - Code analysis with tree-sitter")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--disable-cache", action="store_true", help="Disable parse tree caching")
    parser.add_argument("--version", action="store_true", help="Show version and exit")

    # Parse arguments - this handles --help automatically
    args = parser.parse_args()

    # Handle version display
    if args.version:
        import importlib.metadata

        try:
            version = importlib.metadata.version("mcp-server-tree-sitter")
            print(f"mcp-server-tree-sitter version {version}")
        except importlib.metadata.PackageNotFoundError:
            print("mcp-server-tree-sitter (version unknown - package not installed)")
        sys.exit(0)

    # Set up debug logging if requested
    if args.debug:
        update_log_levels("DEBUG")
        logger.debug("Debug logging enabled")

    # Get the container
    container = get_container()

    # Configure with provided options
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        container.config_manager.load_from_file(args.config)

    if args.disable_cache:
        logger.info("Disabling parse tree cache as requested")
        container.config_manager.update_value("cache.enabled", False)
        container.tree_cache.set_enabled(False)

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
    logger.info("Starting MCP Tree-sitter Server")
    mcp.run()


if __name__ == "__main__":
    main()
