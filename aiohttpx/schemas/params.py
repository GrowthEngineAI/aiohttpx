import httpx
import typing
from aiohttpx.imports.pyd import BaseModel, get_pyd_dict
from aiohttpx.schemas import types as httpxType 

class ClientParams(BaseModel):
    """
    Used to store the params for the Client class
    """
    auth: typing.Optional[httpxType.AuthTypes] = None
    params: typing.Optional[httpxType.QueryParamTypes] = None
    headers: typing.Optional[httpxType.HeaderTypes] = None
    cookies: typing.Optional[httpxType.CookieTypes] = None
    verify: typing.Optional[httpxType.VerifyTypes] = None
    cert: typing.Optional[httpxType.CertTypes] = None
    http1: typing.Optional[bool] = None
    http2: typing.Optional[bool] = None
    proxies: typing.Optional[httpxType.ProxiesTypes] = None

    mounts: typing.Optional[typing.Mapping[str, httpx._client.BaseTransport]] = None
    async_mounts: typing.Optional[typing.Mapping[str, httpx._client.AsyncBaseTransport]] = None

    timeout: typing.Optional[
        typing.Union[typing.Optional[float], typing.Tuple[typing.Optional[float], typing.Optional[float], typing.Optional[float], typing.Optional[float]],
        httpx._client.Timeout,
    ]] = httpx._client.DEFAULT_TIMEOUT_CONFIG
    follow_redirects: typing.Optional[bool] = None
    limits: httpx._client.Limits = httpx._client.DEFAULT_LIMITS
    max_redirects: int = httpx._client.DEFAULT_MAX_REDIRECTS
    event_hooks: typing.Optional[typing.Mapping[str, typing.List[typing.Callable]]] = None
    async_event_hooks: typing.Optional[typing.Mapping[str, typing.List[typing.Callable]]] = None
    base_url: typing.Optional[typing.Union[str, httpx._client.URL]] = ""
    transport: typing.Optional[httpx._client.BaseTransport] = None
    async_transport: typing.Optional[httpx._client.AsyncBaseTransport] = None

    app: typing.Optional[typing.Callable] = None
    trust_env: typing.Optional[bool] = None
    default_encoding: str = "utf-8"
    kwargs: typing.Any = None
    debug: typing.Optional[bool] = None
    soup_enabled: typing.Optional[bool] = None

    @property
    def sync_kwargs(self) -> typing.Dict:
        """
        Returns the sync kwargs
        """
        data = get_pyd_dict(
            self, 
            exclude_none = True, 
            exclude = {'async_transport', 'async_mounts', 'async_event_hooks', 'soup_enabled', 'debug'}
        )
        kwargs = data.pop('kwargs', None)
        if kwargs: data.update(kwargs)
        return data
    
    @property
    def async_kwargs(self) -> typing.Dict:
        """
        Returns the async kwargs
        """
        data = get_pyd_dict(
            self, 
            exclude_none = True, 
            exclude = {'soup_enabled', 'debug'}
        )
        if data.get('async_transport'):
            data['transport'] = data.pop('async_transport', None)
        if data.get('async_mounts'):
            data['mounts'] = data.pop('async_mounts', None)
        if data.get('async_event_hooks'):
            data['event_hooks'] = data.pop('async_event_hooks', None)
        kwargs = data.pop('kwargs', None)
        if kwargs: data.update(kwargs)
        return data
