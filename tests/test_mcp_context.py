"""Tests for mcp_context.py module."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_server_tree_sitter.utils.context.mcp_context import MCPContext, ProgressScope


@pytest.fixture
def mock_mcp_context():
    """Create a mock MCP context."""
    ctx = MagicMock()
    ctx.report_progress = MagicMock()
    ctx.info = MagicMock()
    ctx.warning = MagicMock()
    ctx.error = MagicMock()
    return ctx


def test_progress_scope_init():
    """Test ProgressScope initialization."""
    context = MCPContext()
    scope = ProgressScope(context, 100, "Test operation")

    assert scope.context == context
    assert scope.total == 100
    assert scope.description == "Test operation"
    assert scope.current == 0


def test_progress_scope_update():
    """Test ProgressScope.update."""
    # Create context with spy on report_progress
    context = MagicMock(spec=MCPContext)

    # Create scope
    scope = ProgressScope(context, 100, "Test operation")

    # Test update with default step
    scope.update()
    assert scope.current == 1
    context.report_progress.assert_called_with(1, 100)

    # Test update with custom step
    scope.update(10)
    assert scope.current == 11
    context.report_progress.assert_called_with(11, 100)

    # Test update that would exceed total
    scope.update(200)
    assert scope.current == 100  # Should cap at total
    context.report_progress.assert_called_with(100, 100)


def test_progress_scope_set_progress():
    """Test ProgressScope.set_progress."""
    # Create context with spy on report_progress
    context = MagicMock(spec=MCPContext)

    # Create scope
    scope = ProgressScope(context, 100, "Test operation")

    # Test set_progress
    scope.set_progress(50)
    assert scope.current == 50
    context.report_progress.assert_called_with(50, 100)

    # Test set_progress with value below 0
    scope.set_progress(-10)
    assert scope.current == 0  # Should clamp to 0
    context.report_progress.assert_called_with(0, 100)

    # Test set_progress with value above total
    scope.set_progress(150)
    assert scope.current == 100  # Should clamp to total
    context.report_progress.assert_called_with(100, 100)


def test_mcp_context_init():
    """Test MCPContext initialization."""
    # Test with no context
    context = MCPContext()
    assert context.ctx is None
    assert context.current_step == 0
    assert context.total_steps == 0

    # Test with context
    mock_ctx = MagicMock()
    context = MCPContext(mock_ctx)
    assert context.ctx == mock_ctx


def test_mcp_context_report_progress_with_ctx(mock_mcp_context):
    """Test MCPContext.report_progress with a context."""
    context = MCPContext(mock_mcp_context)

    # Report progress
    context.report_progress(50, 100)

    # Verify state was updated
    assert context.current_step == 50
    assert context.total_steps == 100

    # Verify MCP context was called
    mock_mcp_context.report_progress.assert_called_with(50, 100)


@patch("mcp_server_tree_sitter.utils.context.mcp_context.logger")
def test_mcp_context_report_progress_without_ctx(mock_logger):
    """Test MCPContext.report_progress without a context."""
    context = MCPContext(None)

    # Report progress
    context.report_progress(50, 100)

    # Verify state was updated
    assert context.current_step == 50
    assert context.total_steps == 100

    # Verify logger was called
    mock_logger.debug.assert_called_with("Progress: 50% (50/100)")


@patch("mcp_server_tree_sitter.utils.context.mcp_context.logger")
def test_mcp_context_report_progress_with_exception(mock_logger, mock_mcp_context):
    """Test MCPContext.report_progress when an exception occurs."""
    # Configure mock to raise exception
    mock_mcp_context.report_progress.side_effect = Exception("Test exception")

    context = MCPContext(mock_mcp_context)

    # Report progress - should handle exception
    context.report_progress(50, 100)

    # Verify state was updated
    assert context.current_step == 50
    assert context.total_steps == 100

    # Verify MCP context was called
    mock_mcp_context.report_progress.assert_called_with(50, 100)

    # Verify warning was logged
    mock_logger.warning.assert_called_with("Failed to report progress: Test exception")


@patch("mcp_server_tree_sitter.utils.context.mcp_context.logger")
def test_mcp_context_info(mock_logger, mock_mcp_context):
    """Test MCPContext.info."""
    context = MCPContext(mock_mcp_context)

    # Log info message
    context.info("Test message")

    # Verify logger was called
    mock_logger.info.assert_called_with("Test message")

    # Verify MCP context was called
    mock_mcp_context.info.assert_called_with("Test message")


@patch("mcp_server_tree_sitter.utils.context.mcp_context.logger")
def test_mcp_context_warning(mock_logger, mock_mcp_context):
    """Test MCPContext.warning."""
    context = MCPContext(mock_mcp_context)

    # Log warning message
    context.warning("Test warning")

    # Verify logger was called
    mock_logger.warning.assert_called_with("Test warning")

    # Verify MCP context was called
    mock_mcp_context.warning.assert_called_with("Test warning")


@patch("mcp_server_tree_sitter.utils.context.mcp_context.logger")
def test_mcp_context_error(mock_logger, mock_mcp_context):
    """Test MCPContext.error."""
    context = MCPContext(mock_mcp_context)

    # Log error message
    context.error("Test error")

    # Verify logger was called
    mock_logger.error.assert_called_with("Test error")

    # Verify MCP context was called
    mock_mcp_context.error.assert_called_with("Test error")


@patch("mcp_server_tree_sitter.utils.context.mcp_context.logger")
def test_mcp_context_info_without_ctx(mock_logger):
    """Test MCPContext.info without a context."""
    context = MCPContext(None)

    # Log info message
    context.info("Test message")

    # Verify logger was called
    mock_logger.info.assert_called_with("Test message")


def test_mcp_context_progress_scope():
    """Test MCPContext.progress_scope context manager."""
    # Create context with spies
    context = MagicMock(spec=MCPContext)
    context.report_progress = MagicMock()
    context.info = MagicMock()

    # Use with real MCPContext to test the context manager
    real_context = MCPContext()
    real_context.info = context.info
    real_context.report_progress = context.report_progress

    # Use progress scope
    with real_context.progress_scope(100, "Test operation") as scope:
        # Verify initial state
        context.info.assert_called_with("Starting: Test operation")
        context.report_progress.assert_called_with(0, 100)

        # Update progress
        scope.update(50)
        context.report_progress.assert_called_with(50, 100)

    # Verify final state
    assert context.info.call_args_list[-1][0][0] == "Completed: Test operation"
    context.report_progress.assert_called_with(100, 100)


def test_mcp_context_progress_scope_with_exception():
    """Test MCPContext.progress_scope with an exception in the block."""
    # Create context with spies
    context = MagicMock(spec=MCPContext)
    context.report_progress = MagicMock()
    context.info = MagicMock()

    # Use with real MCPContext to test the context manager
    real_context = MCPContext()
    real_context.info = context.info
    real_context.report_progress = context.report_progress

    # Use progress scope with exception
    try:
        with real_context.progress_scope(100, "Test operation") as scope:
            # Update progress partially
            scope.update(50)
            context.report_progress.assert_called_with(50, 100)

            # Raise exception
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Verify scope was completed despite exception
    assert context.info.call_args_list[-1][0][0] == "Completed: Test operation"
    context.report_progress.assert_called_with(100, 100)


def test_mcp_context_with_mcp_context():
    """Test MCPContext.with_mcp_context."""
    # Create an MCPContext
    context = MCPContext()

    # Create a mock MCP context
    mock_ctx = MagicMock()

    # Create a new context with the mock
    new_context = context.with_mcp_context(mock_ctx)

    # Verify the new context has the mock
    assert new_context.ctx == mock_ctx

    # Verify it's a different instance
    assert new_context is not context


def test_mcp_context_from_mcp_context():
    """Test MCPContext.from_mcp_context."""
    # Create a mock MCP context
    mock_ctx = MagicMock()

    # Create a context from the mock
    context = MCPContext.from_mcp_context(mock_ctx)

    # Verify the context has the mock
    assert context.ctx == mock_ctx

    # Test with None
    context = MCPContext.from_mcp_context(None)
    assert context.ctx is None


def test_mcp_context_try_get_mcp_context():
    """Test MCPContext.try_get_mcp_context."""
    # Create a mock MCP context
    mock_ctx = MagicMock()

    # Create a context with the mock
    context = MCPContext(mock_ctx)

    # Verify try_get_mcp_context returns the mock
    assert context.try_get_mcp_context() == mock_ctx

    # Test with None
    context = MCPContext(None)
    assert context.try_get_mcp_context() is None
