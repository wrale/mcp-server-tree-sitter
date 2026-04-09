"""Query templates for common code patterns by language."""

from typing import Any, Dict, List, Optional, Union

from .templates import QUERY_TEMPLATES


def get_query_template(language: str, template_name: str) -> Optional[str]:
    """
    Get a query template for a language.

    Args:
        language: Language identifier
        template_name: Template name

    Returns:
        Query string or None if not found
    """
    language_templates = QUERY_TEMPLATES.get(language)
    if language_templates:
        return language_templates.get(template_name)
    return None


def list_query_templates(language: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
    """
    List available query templates.

    Args:
        language: Optional language or list of languages to filter by

    Returns:
        Dictionary of templates by language
    """
    if language:
        if isinstance(language, str):
            languages = [lang.strip() for lang in language.split(",")]
        else:
            languages = language
        return {lang: QUERY_TEMPLATES.get(lang, {}) for lang in languages}
    return QUERY_TEMPLATES
