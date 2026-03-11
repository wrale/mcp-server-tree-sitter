"""Tests for the tools.registration module."""

import inspect
from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_tree_sitter.cache.parser_cache import TreeCache
from mcp_server_tree_sitter.config import ConfigurationManager, ServerConfig
from mcp_server_tree_sitter.di import DependencyContainer
from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.project import ProjectRegistry
from mcp_server_tree_sitter.tools.registration import _register_prompts, register_tools

# Type alias for tool/prompt decorator (avoids Any in MockMCPServer)
_Func = Callable[..., object]


class MockMCPServer:
    """Mock MCP server for testing tool registration."""

    def __init__(self) -> None:
        self.tools = {}
        self.prompts = {}

    def tool(self) -> Callable[[_Func], _Func]:
        """Mock tool decorator."""

        def decorator(func: _Func) -> _Func:
            self.tools[func.__name__] = func
            return func

        return decorator

    def prompt(self) -> Callable[[_Func], _Func]:
        """Mock prompt decorator."""

        def decorator(func: _Func) -> _Func:
            self.prompts[func.__name__] = func
            return func

        return decorator


@pytest.fixture
def mock_mcp_server() -> MockMCPServer:
    """Fixture to create a mock MCP server."""
    return MockMCPServer()


@pytest.fixture
def mock_container() -> MagicMock:
    """Fixture to create a mock dependency container (spec=DependencyContainer)."""
    container = MagicMock(spec=DependencyContainer)
    container.config_manager = MagicMock(spec=ConfigurationManager)
    container.project_registry = MagicMock(spec=ProjectRegistry)
    container.language_registry = MagicMock(spec=LanguageRegistry)
    container.tree_cache = MagicMock(spec=TreeCache)

    # Set up config
    mock_config = MagicMock(spec=ServerConfig)
    mock_config.security = MagicMock()
    mock_config.security.max_file_size_mb = 5
    mock_config.cache = MagicMock()
    mock_config.cache.enabled = True
    mock_config.language = MagicMock()
    mock_config.language.default_max_depth = 5
    mock_config.log_level = "INFO"
    container.config_manager.get_config.return_value = mock_config

    return container


def test_register_tools_registers_all_tools(mock_mcp_server: MockMCPServer, mock_container: MagicMock) -> None:
    """Test that register_tools registers all the expected tools."""
    # Call the function
    register_tools(mock_mcp_server)

    # Verify all expected tools are registered
    expected_tools = [
        "configure",
        "register_project_tool",
        "list_projects_tool",
        "remove_project_tool",
        "list_languages",
        "check_language_available",
        "list_files",
        "get_file",
        "get_file_metadata",
        "get_ast",
        "get_node_at_position",
        "get_enclosing_scope",
        "find_text",
        "run_query",
        "get_query_template_tool",
        "list_query_templates_tool",
        "build_query",
        "adapt_query",
        "get_node_types",
        "get_symbols",
        "analyze_project",
        "get_dependencies",
        "analyze_complexity",
        "find_similar_code",
        "find_usage",
        "clear_cache",
    ]

    for tool_name in expected_tools:
        assert tool_name in mock_mcp_server.tools, f"Tool {tool_name} was not registered"


def test_get_enclosing_scope_tool_registered_with_correct_contract(
    mock_mcp_server: MockMCPServer, mock_container: MagicMock
) -> None:
    """After registration, get_enclosing_scope exists and signature/docstring mention project, path, row, column."""
    register_tools(mock_mcp_server)

    assert "get_enclosing_scope" in mock_mcp_server.tools, "Tool get_enclosing_scope was not registered"
    tool_fn = mock_mcp_server.tools["get_enclosing_scope"]

    # Signature or docstring must mention project, path (or file_path), row, column
    doc = (tool_fn.__doc__ or "").lower()
    sig = str(inspect.signature(tool_fn)).lower()
    combined = doc + " " + sig

    assert "project" in combined, "get_enclosing_scope contract should mention project"
    assert "path" in combined or "file_path" in combined, "get_enclosing_scope contract should mention path/file_path"
    assert "row" in combined, "get_enclosing_scope contract should mention row"
    assert "column" in combined, "get_enclosing_scope contract should mention column"


def test_register_prompts_registers_all_prompts(mock_mcp_server: MockMCPServer, mock_container: MagicMock) -> None:
    """Test that _register_prompts registers all the expected prompts."""
    # Call the function
    _register_prompts(mock_mcp_server)

    # Verify all expected prompts are registered
    expected_prompts = [
        "code_review",
        "explain_code",
        "explain_tree_sitter_query",
        "suggest_improvements",
        "project_overview",
    ]

    for prompt_name in expected_prompts:
        assert prompt_name in mock_mcp_server.prompts, f"Prompt {prompt_name} was not registered"


@patch("mcp_server_tree_sitter.tools.analysis_tools.extract_symbols")
def test_get_symbols_tool_calls_extract_symbols(
    mock_extract_symbols: MagicMock,
    mock_mcp_server: MockMCPServer,
    mock_container: MagicMock,
) -> None:
    """Test that the get_symbols tool correctly calls extract_symbols."""
    # Setup
    register_tools(mock_mcp_server)
    mock_extract_symbols.return_value = {"functions": [], "classes": []}

    # Tool resolves container at call time via get_container()
    with patch("mcp_server_tree_sitter.tools.analysis_tools.get_container", return_value=mock_container):
        mock_mcp_server.tools["get_symbols"](project="test_project", file_path="test.py")

    # Verify extract_symbols was called with correct parameters
    mock_extract_symbols.assert_called_once()
    args, _ = mock_extract_symbols.call_args
    assert args[0] == mock_container.project_registry.get_project.return_value
    assert args[1] == "test.py"
    assert args[2] == mock_container.language_registry


@patch("mcp_server_tree_sitter.tools.search_tools.query_code")
def test_run_query_tool_calls_query_code(
    mock_query_code: MagicMock,
    mock_mcp_server: MockMCPServer,
    mock_container: MagicMock,
) -> None:
    """Test that the run_query tool correctly calls query_code."""
    # Setup
    register_tools(mock_mcp_server)
    mock_query_code.return_value = []

    with patch("mcp_server_tree_sitter.tools.search_tools.get_container", return_value=mock_container):
        mock_mcp_server.tools["run_query"](
            project="test_project", query="test query", file_path="test.py", language="python"
        )

    # Verify query_code was called with correct parameters
    mock_query_code.assert_called_once()
    args, _ = mock_query_code.call_args
    assert args[0] == mock_container.project_registry.get_project.return_value
    assert args[1] == "test query"
    assert args[2] == mock_container.language_registry
    assert args[3] == mock_container.tree_cache
    assert args[4] == "test.py"
    assert args[5] == "python"


def test_configure_tool_updates_config(mock_mcp_server: MockMCPServer, mock_container: MagicMock) -> None:
    """Test that the configure tool updates the configuration correctly."""
    # Setup
    register_tools(mock_mcp_server)

    with patch("mcp_server_tree_sitter.tools.project_tools.get_container", return_value=mock_container):
        mock_mcp_server.tools["configure"](cache_enabled=False, max_file_size_mb=10, log_level="DEBUG")

    # Verify the config manager was updated
    mock_container.config_manager.update_value.assert_any_call("cache.enabled", False)
    mock_container.config_manager.update_value.assert_any_call("security.max_file_size_mb", 10)
    mock_container.config_manager.update_value.assert_any_call("log_level", "DEBUG")
    mock_container.tree_cache.set_enabled.assert_called_with(False)


@patch("mcp_server_tree_sitter.tools.file_tools.list_project_files")
def test_list_files_tool_calls_list_project_files(
    mock_list_files: MagicMock,
    mock_mcp_server: MockMCPServer,
    mock_container: MagicMock,
) -> None:
    """Test that the list_files tool correctly calls list_project_files."""
    # Setup
    register_tools(mock_mcp_server)
    mock_list_files.return_value = ["file1.py", "file2.py"]

    with patch("mcp_server_tree_sitter.tools.file_tools.get_container", return_value=mock_container):
        mock_mcp_server.tools["list_files"](project="test_project", pattern="**/*.py")

    # Verify list_project_files was called with correct parameters
    mock_list_files.assert_called_once()
    args, _ = mock_list_files.call_args
    assert args[0] == mock_container.project_registry.get_project.return_value
    assert args[1] == "**/*.py"


@patch("mcp_server_tree_sitter.tools.ast_tools.get_file_ast")
def test_get_ast_tool_calls_get_file_ast(
    mock_get_ast: MagicMock,
    mock_mcp_server: MockMCPServer,
    mock_container: MagicMock,
) -> None:
    """Test that the get_ast tool correctly calls get_file_ast."""
    # Setup
    register_tools(mock_mcp_server)
    mock_get_ast.return_value = {"tree": {}, "file": "test.py", "language": "python"}

    with patch("mcp_server_tree_sitter.tools.ast_tools.get_container", return_value=mock_container):
        mock_mcp_server.tools["get_ast"](project="test_project", path="test.py", max_depth=3)

    # Verify get_file_ast was called with correct parameters
    mock_get_ast.assert_called_once()
    args, kwargs = mock_get_ast.call_args
    assert args[0] == mock_container.project_registry.get_project.return_value
    assert args[1] == "test.py"
    assert args[2] == mock_container.language_registry
    assert args[3] == mock_container.tree_cache
    assert kwargs["max_depth"] == 3
