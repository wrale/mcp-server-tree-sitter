"""Language-specific query templates collection."""

from typing import Dict

from . import (
    apl,
    c,
    cpp,
    go,
    java,
    javascript,
    julia,
    kotlin,
    python,
    rust,
    swift,
    typescript,
)

# Combine all language templates
QUERY_TEMPLATES: Dict[str, Dict[str, str]] = {
    "python": python.TEMPLATES,
    "javascript": javascript.TEMPLATES,
    "typescript": typescript.TEMPLATES,
    "go": go.TEMPLATES,
    "rust": rust.TEMPLATES,
    "c": c.TEMPLATES,
    "cpp": cpp.TEMPLATES,
    "swift": swift.TEMPLATES,
    "java": java.TEMPLATES,
    "kotlin": kotlin.TEMPLATES,
    "julia": julia.TEMPLATES,
    "apl": apl.TEMPLATES,
}
