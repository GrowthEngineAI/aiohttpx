"""
Compatibility code for different versions of Pydantic.
"""
import typing

# Handle v1/v2 of pydantic
try:
    from pydantic import model_validator as root_validator
    from pydantic import validator as _validator

    PYD_VERSION = 2

    def pre_root_validator(*args, **kwargs):
        def decorator(func):
            return root_validator(*args, mode='before', **kwargs)(func)
        return decorator

    def validator(*args, **kwargs):
        def decorator(func):
            return _validator(*args, **kwargs)(classmethod(func))
        return decorator
    
    
except ImportError:
    from pydantic import root_validator, validator

    PYD_VERSION = 1

    def pre_root_validator(*args, **kwargs):
        def decorator(func):
            return root_validator(*args, pre=True, **kwargs)(func)
        return decorator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    if PYD_VERSION == 2:
        # Install pydantic-settings if it's not available
        from aiohttpx.utils.imports import install_library
        install_library('pydantic-settings', verbose = True)
        from pydantic_settings import BaseSettings

    else:
        from pydantic import BaseSettings

from pydantic import BaseModel as _BaseModel

class BaseModel(_BaseModel):

    class Config:
        extra = 'allow'
        arbitrary_types_allowed = True



def get_pyd_dict(model: BaseModel, **kwargs) -> typing.Dict[str, typing.Any]:
    """
    Get a dict from a pydantic model
    """
    return model.model_dump(**kwargs) if PYD_VERSION == 2 else model.dict(**kwargs)

