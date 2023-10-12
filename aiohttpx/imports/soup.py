
"""
Import Handler for bs4
"""


from aiohttpx.utils.imports import resolve_missing, require_missing_wrapper

try:
    from bs4 import BeautifulSoup
    from bs4.element import Tag
    _bs4_available = True
except ImportError:
    BeautifulSoup = object
    Tag = object
    _bs4_available = False

def resolve_bs4(
    required: bool = False,
):
    """
    Ensures that `bs4` is available
    """
    global _bs4_available, BeautifulSoup, Tag
    if not _bs4_available:
        resolve_missing('bs4', required = required)
        from bs4 import BeautifulSoup
        from bs4.element import Tag
        _bs4_available = True


def require_bs4(
    required: bool = False,
):
    """
    Wrapper for `resolve_bs4` that can be used as a decorator
    """
    def decorator(func):
        return require_missing_wrapper(
            resolver = resolve_bs4, 
            func = func, 
            required = required
        )
    return decorator