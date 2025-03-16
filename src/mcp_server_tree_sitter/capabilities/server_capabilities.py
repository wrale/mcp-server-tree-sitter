"""Server capability declarations for MCP integration."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def register_capabilities(mcp_server: Any) -> None:
    """
    Register MCP server capabilities.

    Args:
        mcp_server: MCP server instance
    """
    # Avoid circular imports
    from ..config import CONFIG

    # FastMCP may not have capability method, so we'll skip this for now
    # @mcp_server.capability("prompts.listChanged")
    def handle_prompts_list_changed() -> Dict[str, Any]:
        """Handle prompt template management events."""
        logger.debug("Received prompts.listChanged event")
        return {"status": "success"}

    # @mcp_server.capability("resources.subscribe")
    def handle_resources_subscribe(resource_uri: str) -> Dict[str, Any]:
        """
        Handle resource subscription requests.

        Args:
            resource_uri: Resource URI to subscribe to

        Returns:
            Subscription response
        """
        logger.debug(f"Received subscription request for {resource_uri}")
        return {"status": "success", "resource": resource_uri}

    # @mcp_server.capability("resources.listChanged")
    def handle_resources_list_changed() -> Dict[str, Any]:
        """Handle resource discovery events."""
        logger.debug("Received resources.listChanged event")
        return {"status": "success"}

    # @mcp_server.capability("tools.listChanged")
    def handle_tools_list_changed() -> Dict[str, Any]:
        """Handle tool discovery events."""
        logger.debug("Received tools.listChanged event")
        return {"status": "success"}

    # @mcp_server.capability("logging")
    def handle_logging(level: str, message: str) -> Dict[str, Any]:
        """
        Handle logging configuration.

        Args:
            level: Log level
            message: Log message

        Returns:
            Logging response
        """
        log_levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }

        log_level = log_levels.get(level.lower(), logging.INFO)
        logger.log(log_level, f"MCP: {message}")

        return {"status": "success"}

    # @mcp_server.capability("completion")
    def handle_completion(text: str, position: int) -> Dict[str, Any]:
        """
        Handle argument completion suggestions.

        Args:
            text: Current input text
            position: Cursor position in text

        Returns:
            Completion suggestions
        """
        # Simple completion for commonly used arguments
        suggestions: List[Dict[str, str]] = []

        # Extract the current word being typed
        current_word = ""
        i = position - 1
        while i >= 0 and text[i].isalnum() or text[i] == "_":
            current_word = text[i] + current_word
            i -= 1

        # Project name suggestions
        if current_word and "project" in text[:position].lower():
            from ..models.project import ProjectRegistry

            registry = ProjectRegistry()
            for project_dict in registry.list_projects():
                project_name = project_dict["name"]
                if project_name.startswith(current_word):
                    suggestions.append(
                        {
                            "text": project_name,
                            "description": f"Project: {project_name}",
                        }
                    )

        # Language suggestions
        if current_word and "language" in text[:position].lower():
            from ..language.registry import LanguageRegistry

            language_registry = LanguageRegistry()
            for language in language_registry.list_available_languages():
                if language.startswith(current_word):
                    suggestions.append({"text": language, "description": f"Language: {language}"})

        # Config suggestions
        if current_word and "config" in text[:position].lower():
            if "cache_enabled".startswith(current_word):
                suggestions.append(
                    {
                        "text": "cache_enabled",
                        "description": f"Cache enabled: {CONFIG.cache.enabled}",
                    }
                )
            if "max_file_size_mb".startswith(current_word):
                # Store in variable to avoid line length error
                size_mb = CONFIG.security.max_file_size_mb
                suggestions.append(
                    {
                        "text": "max_file_size_mb",
                        "description": f"Max file size: {size_mb} MB",
                    }
                )
            if "log_level".startswith(current_word):
                suggestions.append(
                    {
                        "text": "log_level",
                        "description": f"Log level: {CONFIG.log_level}",
                    }
                )

        return {"suggestions": suggestions}
