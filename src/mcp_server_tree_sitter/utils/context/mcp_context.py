"""Context handling for MCP operations with progress reporting."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Protocol, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MCPContextProtocol(Protocol):
    """Protocol for MCP context objects that support progress and info reporting."""

    def report_progress(self, current: int, total: int) -> None:
        """Report progress to the MCP client."""
        ...

    def info(self, message: str) -> None:
        """Log or send an info message."""
        ...

    def warning(self, message: str) -> None:
        """Log or send a warning message."""
        ...

    def error(self, message: str) -> None:
        """Log or send an error message."""
        ...


class ProgressScope:
    """Scope for tracking progress of an operation."""

    def __init__(self, context: "MCPContext", total: int, description: str) -> None:
        """
        Initialize a progress scope.

        Args:
            context: The parent MCPContext
            total: Total number of steps
            description: Description of the operation
        """
        self.context = context
        self.total = total
        self.description = description
        self.current = 0

    def update(self, step: int = 1) -> None:
        """
        Update progress by a number of steps.

        Args:
            step: Number of steps to add to progress
        """
        self.current += step
        if self.current > self.total:
            self.current = self.total
        self.context.report_progress(self.current, self.total)

    def set_progress(self, current: int) -> None:
        """
        Set progress to a specific value.

        Args:
            current: Current progress value
        """
        self.current = max(0, min(current, self.total))
        self.context.report_progress(self.current, self.total)


class MCPContext:
    """Context for MCP operations with progress reporting."""

    def __init__(self, ctx: "MCPContextProtocol" | None = None) -> None:
        """
        Initialize context with optional MCP context.

        Args:
            ctx: MCP context object, if available
        """
        self.ctx = ctx
        self.total_steps = 0
        self.current_step = 0

    def report_progress(self, current: int, total: int) -> None:
        """
        Report progress to the MCP client.

        Args:
            current: Current progress value
            total: Total steps
        """
        self.current_step = current
        self.total_steps = total

        if self.ctx and hasattr(self.ctx, "report_progress"):
            # Use MCP context if available
            try:
                self.ctx.report_progress(current, total)
            except (OSError, RuntimeError, ConnectionError, AttributeError) as e:
                logger.warning("Failed to report progress: %s", e)
            except Exception as e:
                logger.exception("Unexpected error reporting progress: %s", e)
        else:
            # Log progress if no MCP context
            if total > 0:
                percentage = int((current / total) * 100)
                logger.debug(f"Progress: {percentage}% ({current}/{total})")

    def info(self, message: str) -> None:
        """
        Log an info message.

        Args:
            message: Message to log
        """
        logger.info(message)
        if self.ctx and hasattr(self.ctx, "info"):
            try:
                self.ctx.info(message)
            except (OSError, RuntimeError, ConnectionError, AttributeError) as e:
                logger.warning("Failed to send info message: %s", e)
            except Exception as e:
                logger.exception("Unexpected error sending info message: %s", e)

    def warning(self, message: str) -> None:
        """
        Log a warning message.

        Args:
            message: Message to log
        """
        logger.warning(message)
        if self.ctx and hasattr(self.ctx, "warning"):
            try:
                self.ctx.warning(message)
            except (OSError, RuntimeError, ConnectionError, AttributeError) as e:
                logger.warning("Failed to send warning message: %s", e)
            except Exception as e:
                logger.exception("Unexpected error sending warning message: %s", e)

    def error(self, message: str) -> None:
        """
        Log an error message.

        Args:
            message: Message to log
        """
        logger.error(message)
        if self.ctx and hasattr(self.ctx, "error"):
            try:
                self.ctx.error(message)
            except (OSError, RuntimeError, ConnectionError, AttributeError) as e:
                logger.warning("Failed to send error message: %s", e)
            except Exception as e:
                logger.exception("Unexpected error sending error message: %s", e)

    @contextmanager
    def progress_scope(self, total: int, description: str) -> Generator[ProgressScope, None, None]:
        """
        Context manager for tracking progress of an operation.

        Args:
            total: Total number of steps
            description: Description of the operation

        Yields:
            ProgressScope object for updating progress
        """
        try:
            self.info(f"Starting: {description}")
            scope = ProgressScope(self, total, description)
            scope.update(0)  # Set initial progress to 0
            yield scope
        finally:
            if scope.current < scope.total:
                scope.set_progress(scope.total)  # Ensure we complete the progress
            self.info(f"Completed: {description}")

    def with_mcp_context(self, ctx: "MCPContextProtocol") -> "MCPContext":
        """
        Create a new context with the given MCP context.

        Args:
            ctx: MCP context object

        Returns:
            New MCPContext with the given MCP context
        """
        return MCPContext(ctx)

    @staticmethod
    def from_mcp_context(ctx: "MCPContextProtocol" | None) -> "MCPContext":
        """
        Create a context from an MCP context.

        Args:
            ctx: MCP context object or None

        Returns:
            New MCPContext
        """
        return MCPContext(ctx)

    def try_get_mcp_context(self) -> "MCPContextProtocol" | None:
        """
        Get the wrapped MCP context if available.

        Returns:
            MCP context or None
        """
        return self.ctx
