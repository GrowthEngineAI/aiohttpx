"""
Base Import Handler
"""
import sys
import typing
import functools
import importlib
import subprocess
from types import ModuleType

from .logs import logger
from .helpers import is_coro_func

def is_lib_available(library: str) -> bool:
    """ Checks whether a Python Library is available."""
    import pkg_resources
    if library == 'colab': library = 'google.colab'
    try:
        _ = pkg_resources.get_distribution(library)
        return True
    except pkg_resources.DistributionNotFound: return False

def get_lib_requirement(name: str, clean: bool = True) -> str:
    # Replaces '-' with '_'
    # for any library such as tensorflow-text -> tensorflow_text
    name = name.replace('-', '_')
    return name.split('=')[0].replace('>', '').replace('<', '').strip() if clean else name.strip()


def is_imported(library: str) -> bool:
    """ Checks whether a Python Library is currently imported."""
    return library in sys.modules

def ensure_lib_imported(library: str):
    clean_lib = get_lib_requirement(library, True)
    if not is_imported(clean_lib): sys.modules[clean_lib] = importlib.import_module(clean_lib)
    return sys.modules[clean_lib]

def install_library(library: str, upgrade: bool = True, verbose: bool = False):
    """
    Install the library
    """
    pip_exec = [sys.executable, '-m', 'pip', 'install']
    msg = f"Installing {library}"
    if '=' not in library or upgrade: 
        pip_exec.append('--upgrade')
        msg += ' (upgrade=True)'
    if verbose: logger.info(msg)
    pip_exec.append(library)
    return subprocess.check_call(pip_exec, stdout=subprocess.DEVNULL)

def import_lib(
    library: str, 
    pip_name: str = None, 
    resolve_missing: bool = True, 
    require: bool = False, 
    upgrade: bool = False
) -> ModuleType:
    """ Lazily resolves libs.

        if pip_name is provided, will install using pip_name, otherwise will use libraryname

        ie ->   import_lib('fuse', 'fusepy') # if fusepy is not expected to be available, and fusepy is the pip_name
                import_lib('fuse') # if fusepy is expected to be available
        
        returns `fuse` as if you ran `import fuse`
    
        if available, returns the sys.modules[library]
        if missing and resolve_missing = True, will lazily install
    else:
        if require: raise ImportError
        returns None
    """
    clean_lib = get_lib_requirement(library, True)
    if not is_lib_available(clean_lib):
        if require and not resolve_missing: raise ImportError(f"Required Lib {library} is not available.")
        if not resolve_missing: return None
        install_library(pip_name or library, upgrade=upgrade)
    return ensure_lib_imported(library)

def resolve_missing(
    modules: typing.Union[str, typing.List[str]],
    packages: typing.Union[str, typing.List[str]] = None,
    required: bool = True,
):
    """
    Resolves missing libraries
    """
    if not isinstance(modules, list):
        modules = [modules]
    if packages is not None and not isinstance(packages, list):
        packages = [packages]
    elif packages is None:
        packages = modules
    kind = 'required' if required else 'optionally required'
    logger.info(f"{', '.join(modules)} are {kind}. Installing...")
    for module, pkg in zip(modules, packages):
        import_lib(module, pkg)


def resolve_missing_custom(
    modules: typing.Union[str, typing.List[str]],
    packages: typing.Union[str, typing.List[str]] = None,
    required: bool = True,
):
    """
    Handles custom use cases like `torch` where we need to
    have a extra index to install from
    """
    if not isinstance(modules, list):
        modules = [modules]
    if packages is not None and not isinstance(packages, list):
        packages = [packages]
    elif packages is None:
        packages = modules
    
    module_names = [module.split(' ', 1)[0] for module in modules]
    kind = 'required' if required else 'optionally required'
    logger.info(f"{', '.join(module_names)} are {kind}. Installing...")
    for module, pkg in zip(modules, packages):
        module_name = get_lib_requirement(module, True)
        if is_lib_available(module_name):
            continue
        install_library(pkg)

    
def require_missing_wrapper(
    resolver: typing.Callable,
    func: typing.Callable,
    **resolver_kwargs,
):
    """
    Helper function to wrap the resolve async or sync funcs
    """
    if is_coro_func(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            resolver(**resolver_kwargs)
            return await func(*args, **kwargs)
    else:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            resolver(**resolver_kwargs)
            return func(*args, **kwargs)

    return wrapper