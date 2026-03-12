"""Query templates for common code patterns by language.

Templates are loaded from per-language data (language/data/) via the loader.
"""

from typing import Any, Dict

from .loader import get_query_templates


def get_query_template(language: str, template_name: str) -> str | None:
    """
    Get a query template for a language.

    Args:
        language: Language identifier
        template_name: Template name

    Returns:
        Query string or None if not found
    """
    templates = get_query_templates()
    language_templates = templates.get(language)
    if language_templates:
        return language_templates.get(template_name)
    return None


def list_query_templates(language: str | None = None) -> Dict[str, Any]:
    """
    List available query templates.

    Args:
        language: Optional language to filter by

    Returns:
        Dictionary of templates by language
    """
    templates = get_query_templates()
    if language:
        return {language: templates.get(language, {})}
    return templates
