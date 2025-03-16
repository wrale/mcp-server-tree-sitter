"""Language-specific query templates collection."""

from typing import Dict, Any

from . import python
from . import javascript
from . import typescript
from . import go
from . import rust
from . import c
from . import cpp
from . import swift
from . import java
from . import kotlin
from . import julia
from . import apl

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
