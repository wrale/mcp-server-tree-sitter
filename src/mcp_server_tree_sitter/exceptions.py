"""Exception classes for mcp-server-tree-sitter."""


class MCPTreeSitterError(Exception):
    """Base exception for mcp-server-tree-sitter."""

    pass


class LanguageError(MCPTreeSitterError):
    """Errors related to tree-sitter languages."""

    pass


class LanguageNotFoundError(LanguageError):
    """Raised when a language parser is not available."""

    pass


class LanguageInstallError(LanguageError):
    """Raised when language installation fails."""

    pass


class ParsingError(MCPTreeSitterError):
    """Errors during parsing."""

    pass


class ProjectError(MCPTreeSitterError):
    """Errors related to project management."""

    pass


class FileAccessError(MCPTreeSitterError):
    """Errors accessing project files."""

    pass


class QueryError(MCPTreeSitterError):
    """Errors related to tree-sitter queries."""

    pass


class SecurityError(MCPTreeSitterError):
    """Security-related errors."""

    pass


class CacheError(MCPTreeSitterError):
    """Errors related to caching."""

    pass
