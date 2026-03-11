"""Pydantic schema and abstract base for per-language data files.

Each supported language is defined in a single data file under language/data/
by a class that subclasses LanguageDataBase and sets class attributes.
Loading validates via LanguageData. Scope kinds match ScopeKind in scope_node_types.py.
"""

from abc import ABC
from typing import ClassVar, Literal, Type

from pydantic import BaseModel, Field, model_validator

# Canonical scope kinds; must match ScopeKind in scope_node_types.py
ScopeKindKey = Literal["function", "class", "module"]

_REQUIRED_SCOPE_KINDS: tuple[ScopeKindKey, ...] = ("function", "class", "module")

# Single source of truth for default symbol types when a language has none or is unknown
DEFAULT_SYMBOL_TYPES: list[str] = ["functions", "classes", "imports"]


class LanguageDataBase(ABC):
    """Abstract base for per-language data. Subclass in language/data/<id>.py and set class attributes.
    Subclasses register themselves automatically via __init_subclass__.
    """

    _registry: ClassVar[list[Type["LanguageDataBase"]]] = []

    id: ClassVar[str]
    extensions: ClassVar[list[str]]
    scope_node_types: ClassVar[dict[ScopeKindKey, list[str]]]
    query_templates: ClassVar[dict[str, str]]
    node_type_descriptions: ClassVar[dict[str, str]]
    # Optional: default symbol types for extraction when not specified. Use [] to inherit default.
    default_symbol_types: ClassVar[list[str]] = []
    # Optional: tree-sitter node types that count as decision points for cyclomatic complexity (e.g. if_statement, for_statement).
    complexity_nodes: ClassVar[list[str]] = []

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not LanguageDataBase:
            LanguageDataBase._registry.append(cls)

    @classmethod
    def registered_subclasses(cls) -> list[Type["LanguageDataBase"]]:
        """Return all registered subclasses (for use by the loader)."""
        return list(LanguageDataBase._registry)

    @classmethod
    def to_language_data(cls) -> "LanguageData":
        """Build and validate a LanguageData instance from this class's attributes."""
        default_syms = getattr(cls, "default_symbol_types", [])
        complexity_nodes = getattr(cls, "complexity_nodes", [])
        return LanguageData(
            id=cls.id,
            extensions=list(cls.extensions),
            scope_node_types={k: list(v) for k, v in cls.scope_node_types.items()},
            query_templates=dict(cls.query_templates),
            node_type_descriptions=getattr(cls, "node_type_descriptions", {}) or {},
            default_symbol_types=list(default_syms) if default_syms else DEFAULT_SYMBOL_TYPES,
            complexity_nodes=list(complexity_nodes),
        )


class LanguageData(BaseModel):
    """Schema for one language's data (one file per language under language/data/)."""

    id: str = Field(..., description="Language identifier, e.g. 'python', 'javascript'")
    extensions: list[str] = Field(
        ...,
        min_length=1,
        description="File extensions that map to this language (e.g. ['py'] for Python)",
    )
    scope_node_types: dict[ScopeKindKey, list[str]] = Field(
        ...,
        description="Canonical scope kind -> tree-sitter node type names for enclosure resolution",
    )
    query_templates: dict[str, str] = Field(
        ...,
        description="Named query template -> tree-sitter query string",
    )
    node_type_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description="Optional: node type name -> short description for tooling/docs",
    )
    default_symbol_types: list[str] = Field(
        default_factory=lambda: list(DEFAULT_SYMBOL_TYPES),
        description="Default symbol types for extraction when not specified",
    )
    complexity_nodes: list[str] = Field(
        default_factory=list,
        description="Tree-sitter node types that count as decision points for cyclomatic complexity",
    )

    @model_validator(mode="after")
    def _check_scope_kinds(self) -> "LanguageData":
        """Ensure scope_node_types has exactly the three required keys."""
        for key in _REQUIRED_SCOPE_KINDS:
            if key not in self.scope_node_types:
                raise ValueError(f"scope_node_types must contain key {key!r}")
        for key in self.scope_node_types:
            if key not in _REQUIRED_SCOPE_KINDS:
                raise ValueError(f"scope_node_types has unknown key {key!r}; allowed: {_REQUIRED_SCOPE_KINDS}")
        return self
