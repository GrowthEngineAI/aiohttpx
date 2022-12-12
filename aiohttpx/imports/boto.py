"""
Import Handler for boto3, botocore, aioboto3, aiobotocore
"""

try:
    from botocore.exceptions import ClientError
    from botocore.exceptions import EndpointConnectionError
    _botocore_avail = True

except ImportError:
    ClientError = Exception
    EndpointConnectionError = Exception
    _botocore_avail = False

try:
    from boto3.session import Session as BotoSession
    _boto3_avail = True
except ImportError:
    BotoSession = object
    _boto3_avail = False

try:
    from aiobotocore.client import BaseClient as AsyncBotoClient
    from aioboto3.session import Session as AsyncBotoSession
    _aioboto_avail = True

except ImportError:
    AsyncBotoClient = object
    AsyncBotoSession = object
    _aioboto_avail = False


from lazyops.utils import resolve_missing, require_missing_wrapper

def resolve_botocore(
    required: bool = True,
):
    """
    Ensures that `botocore` is available
    """
    global _botocore_avail
    global ClientError, EndpointConnectionError
    if not _botocore_avail:
        resolve_missing('botocore', required = required)
        from botocore.exceptions import ClientError
        from botocore.exceptions import EndpointConnectionError
        _botocore_avail = True

def resolve_boto3(
    required: bool = True,
):
    """
    Ensures that `boto3` is available
    """
    global _boto3_avail
    global BotoSession
    if not _boto3_avail:
        resolve_missing('boto3', required = required)
        from boto3.session import Session as BotoSession
        _boto3_avail = True

def resolve_aioboto(
    required: bool = True,
):
    """
    Ensures that `aioboto3` and `aiobotocore` are available
    """
    global _aioboto_avail
    global AsyncBotoClient, AsyncBotoSession
    if not _aioboto_avail:
        resolve_missing(['aiobotocore', 'aioboto3'], required = required)
        from aiobotocore.client import BaseClient as AsyncBotoClient
        from aioboto3.session import Session as AsyncBotoSession
        _aioboto_avail = True

def resolve_boto(
    is_async: bool = True,
    required: bool = True,
):
    """
    Ensures that `boto3` and `botocore` are available
    """
    resolve_botocore(required = required)
    if is_async:
        resolve_aioboto(required = required)
    else:
        resolve_boto3(required = required)


def require_boto(
    is_async: bool = True,
    required: bool = True,
):
    """
    Wrapper for `resolve_boto` that can be used as a decorator
    """
    def decorator(func):
        return require_missing_wrapper(
            resolver = resolve_boto, 
            func = func, 
            is_async = is_async, 
            required = required
        )
    return decorator