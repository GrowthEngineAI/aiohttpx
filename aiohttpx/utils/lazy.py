"""
Lazy Imports
"""

from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from aiohttpx.configs.base import AiohttpxSettings


_aiohttpx_settings: Optional["AiohttpxSettings"] = None

def get_aiohttpx_settings() -> "AiohttpxSettings":
    """
    Returns the aiohttpx settings
    """
    global _aiohttpx_settings

    if _aiohttpx_settings is None:
        from aiohttpx.configs.base import AiohttpxSettings
        _aiohttpx_settings = AiohttpxSettings()

    return _aiohttpx_settings