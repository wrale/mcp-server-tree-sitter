"""Main entry point for mcp-server-tree-sitter."""

import argparse
import logging
import sys

from .config import load_config
from .context import global_context
from .server import mcp

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    """Run the server with optional arguments."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Tree-sitter Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--disable-cache", action="store_true", help="Disable parse tree caching")

    args = parser.parse_args()

    # Set up logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Load configuration
    try:
        config = load_config(args.config)

        # Update global context with config
        if args.config:
            global_context.config_manager.load_from_file(args.config)
        else:
            # Update individual settings from config
            global_context.config_manager.update_value("cache.enabled", config.cache.enabled)
            global_context.config_manager.update_value("cache.max_size_mb", config.cache.max_size_mb)
            global_context.config_manager.update_value("security.max_file_size_mb", config.security.max_file_size_mb)
            global_context.config_manager.update_value("language.default_max_depth", config.language.default_max_depth)

        logger.debug("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1

    # Run the server
    try:
        logger.info("Starting MCP Tree-sitter Server (with state persistence)")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
