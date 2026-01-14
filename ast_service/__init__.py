"""Simple AST service package

Public API:
- parse_code(code: str, language: str='python') -> dict

This package is designed to be easily extended with additional language parsers
using the registry in `registry.py`.
"""
from .registry import registry
# Import language implementations so they register themselves on package import
from . import python_parser  # noqa: F401

__all__ = ["parse_code", "registry"]


def parse_code(code: str, language: str = "python") -> dict:
    """Parse code for a given language and return a serializable compact AST dict.

    Parsers MUST return the compact representation by default.

    Raises ValueError if no parser is registered for the requested language.
    """
    parser = registry.get(language)
    if parser is None:
        raise ValueError(f"No parser registered for language '{language}'")
    return parser.parse(code)
