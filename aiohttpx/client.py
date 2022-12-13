import httpx
import typing
from contextlib import asynccontextmanager, contextmanager, suppress
from lazyops.types import lazyproperty
from aiohttpx.utils import logger

from aiohttpx.imports.soup import (
    BeautifulSoup,
    resolve_bs4,
)
from aiohttpx.schemas.params import ClientParams
from aiohttpx.schemas import types as httpxType

# Monkey patching httpx.Response to add soup property
# that way it is only called when the property is accessed
# rather than on every request

@lazyproperty
def soup_property(self):
    resolve_bs4(required = False)
    with suppress(Exception):
        return BeautifulSoup(self.text, 'html.parser')

def wrap_soup_response(response: httpx.Response) -> httpx.Response:
    setattr(response.__class__, 'soup', soup_property)
    return response


class Client:

    """
    An sync + asynchronous HTTP client, with connection pooling, HTTP/2, redirects,
    cookie persistence, etc.

    Usage:

    ```python
    >>> async with aiohttpx.Client() as client:
    >>>     response = await client.async_get('https://example.org')
    ```

    **Parameters:**

    * **auth** - *(optional)* An authentication class to use when sending
    requests.
    * **params** - *(optional)* Query parameters to include in request URLs, as
    a string, dictionary, or sequence of two-tuples.
    * **headers** - *(optional)* Dictionary of HTTP headers to include when
    sending requests.
    * **cookies** - *(optional)* Dictionary of Cookie items to include when
    sending requests.
    * **verify** - *(optional)* SSL certificates (a.k.a CA bundle) used to
    verify the identity of requested hosts. Either `True` (default CA bundle),
    a path to an SSL certificate file, or `False` (disable verification).
    * **cert** - *(optional)* An SSL certificate used by the requested host
    to authenticate the client. Either a path to an SSL certificate file, or
    two-tuple of (certificate file, key file), or a three-tuple of (certificate
    file, key file, password).
    * **http2** - *(optional)* A boolean indicating if HTTP/2 support should be
    enabled. Defaults to `False`.
    * **proxies** - *(optional)* A dictionary mapping HTTP protocols to proxy
    URLs.
    * **timeout** - *(optional)* The timeout configuration to use when sending
    requests.
    * **limits** - *(optional)* The limits configuration to use.
    * **max_redirects** - *(optional)* The maximum number of redirect responses
    that should be followed.
    * **base_url** - *(optional)* A URL to use as the base when building
    request URLs.
    * **transport** - *(optional)* [Sync] A transport class to use for sending requests
    over the network.
    * **async_transport** - *(optional)* [Async] A transport class to use for sending requests
    over the network.
    * **app** - *(optional)* An ASGI application to send requests to,
    rather than sending actual network requests.
    * **trust_env** - *(optional)* Enables or disables usage of environment
    variables for configuration.
    * **default_encoding** - *(optional)* The default encoding to use for decoding
    response text, if no charset information is included in a response Content-Type
    header. Set to a callable for automatic character set detection. Default: "utf-8".
    """

    def __init__(
        self,
        *,
        auth: typing.Optional[httpxType.AuthTypes] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        verify: typing.Optional[httpxType.VerifyTypes] = None,
        cert: typing.Optional[httpxType.CertTypes] = None,
        http1: typing.Optional[bool] = None,
        http2: typing.Optional[bool] = None,
        proxies: typing.Optional[httpxType.ProxiesTypes] = None,

        mounts: typing.Optional[typing.Mapping[str, httpxType.BaseTransport]] = None,
        async_mounts: typing.Optional[typing.Mapping[str, httpxType.AsyncBaseTransport]] = None,

        timeout: httpxType.TimeoutTypes = httpxType.DEFAULT_TIMEOUT_CONFIG,
        follow_redirects: typing.Optional[bool] = None,
        limits: httpxType.Limits = httpxType.DEFAULT_LIMITS,
        max_redirects: int = httpxType.DEFAULT_MAX_REDIRECTS,
        event_hooks: typing.Optional[
            typing.Mapping[str, typing.List[typing.Callable]]
        ] = None,
        base_url: httpxType.URLTypes = "",
        
        transport: typing.Optional[httpxType.BaseTransport] = None,
        async_transport: typing.Optional[httpxType.AsyncBaseTransport] = None,

        app: typing.Optional[typing.Callable] = None,
        trust_env: typing.Optional[bool] = None,
        default_encoding: str = "utf-8",
        soup_enabled: typing.Optional[bool] = None,
        debug: typing.Optional[bool] = None,
        **kwargs
    ):
        self._config = ClientParams(
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            proxies=proxies,
            mounts=mounts,
            async_mounts=async_mounts,
            timeout=timeout,
            follow_redirects=follow_redirects,
            limits=limits,
            max_redirects=max_redirects,
            event_hooks=event_hooks,
            base_url=base_url,
            transport=transport,
            async_transport=async_transport,
            app=app,
            trust_env=trust_env,
            default_encoding=default_encoding,
            soup_enabled=soup_enabled,
            debug=debug,
            kwargs=kwargs
        )
        self._sync_client: httpx.Client = None
        self._async_client: httpx.AsyncClient = None
        self._sync_active: bool = False
        self._async_active: bool = False

    @property
    def async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or not self._async_active:
            self._async_client = httpx.AsyncClient(
                **self._config.async_kwargs
            )
            self._async_active = True
        return self._async_client

    @property
    def sync_client(self) -> httpx.Client:
        if self._sync_client is None or not self._sync_active:
            self._sync_client = httpx.Client(
                **self._config.sync_kwargs
            )
            self._sync_active = True
        return self._sync_client
    
    @property
    def base_url(self) -> typing.Union[str, httpx.URL]:
        if self._async_client:
            return self._async_client.base_url
        return self._sync_client.base_url if self._sync_client else self._config.base_url
    
    @property
    def headers(self) -> typing.Dict[str, str]:
        if self._async_client:
            return self._async_client.headers
        return self._sync_client.headers if self._sync_client else self._config.headers

    @property
    def params(self) -> typing.Dict[str, str]:
        if self._async_client:
            return self._async_client.params
        return self._sync_client.params if self._sync_client else self._config.params
    
    @property
    def cookies(self) -> typing.Dict[str, str]:
        if self._async_client:
            return self._async_client.cookies
        return self._sync_client.cookies if self._sync_client else self._config.cookies
    
    @property
    def auth(self) -> typing.Optional[httpxType.AuthTypes]:
        if self._async_client:
            return self._async_client.auth
        return self._sync_client.auth if self._sync_client else self._config.auth
    
    @property
    def timeout(self) -> httpxType.TimeoutTypes:
        if self._async_client:
            return self._async_client.timeout
        return self._sync_client.timeout if self._sync_client else self._config.timeout

    @property
    def event_hooks(self) -> typing.Optional[typing.Mapping[str, typing.List[typing.Callable]]]:
        if self._async_client:
            return self._async_client.event_hooks
        return self._sync_client.event_hooks if self._sync_client else self._config.event_hooks

    def set_auth(self, auth: httpxType.AuthTypes):
        if self._async_client:
            self._async_client.auth = auth
        if self._sync_client:
            self._sync_client.auth = auth
        self._config.auth = auth
    
    def set_base_url(self, base_url: httpxType.URLTypes):
        if isinstance(base_url, str): base_url = httpx.URL(base_url)
        if self._async_client:
            self._async_client.base_url = base_url
        if self._sync_client:
            self._sync_client.base_url = base_url
        self._config.base_url = str(base_url)
    
    def set_headers(self, headers: httpxType.HeaderTypes):
        if self._async_client:
            self._async_client.headers = headers
        if self._sync_client:
            self._sync_client.headers = headers
        self._config.headers = headers
    
    def set_params(self, params: httpxType.QueryParamTypes):
        if self._async_client:
            self._async_client.params = params
        if self._sync_client:
            self._sync_client.params = params
        self._config.params = params
    
    def set_cookies(self, cookies: httpxType.CookieTypes):
        if self._async_client:
            self._async_client.cookies = cookies
        if self._sync_client:
            self._sync_client.cookies = cookies
        self._config.cookies = cookies
    
    def set_timeout(self, timeout: httpxType.TimeoutTypes):
        if self._async_client:
            self._async_client.timeout = timeout
        if self._sync_client:
            self._sync_client.timeout = timeout
        self._config.timeout = timeout
    
    def set_event_hooks(self, event_hooks: typing.Mapping[str, typing.List[typing.Callable]]):
        if self._async_client:
            self._async_client.event_hooks = event_hooks
        if self._sync_client:
            self._sync_client.event_hooks = event_hooks
        self._config.event_hooks = event_hooks

    def build_request(
        self,
        method: str,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Request:
        """
        Build and return a request instance.

        * The `params`, `headers` and `cookies` arguments
        are merged with any values set on the client.
        * The `url` argument is merged with any `base_url` set on the client.

        See also: [Request instances][0]

        [0]: /advanced/#request-instances
        """
        return self.sync_client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )
    
    async def async_build_request(
        self,
        method: str,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Request:
        """
        Build and return a request instance.

        * The `params`, `headers` and `cookies` arguments
        are merged with any values set on the client.
        * The `url` argument is merged with any `base_url` set on the client.

        See also: [Request instances][0]

        [0]: /advanced/#request-instances
        """
        return self.async_client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )

    """
    Async Methods
    """
    async def async_send(
        self,
        request: httpx.Request,
        *args,
        stream: bool = False,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault, None] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        """
        Send a request.

        The request is sent as-is, unmodified.

        Typically you'll want to build one with `Client.build_request()`
        so that any client-level configuration is merged into the request,
        but passing an explicit `httpx.Request()` is supported as well.

        See also: [Request instances][0]

        [0]: /advanced/#request-instances
        """
        return await self.async_client.send(
            request,
            *args,
            stream=stream,
            auth=auth,
            follow_redirects=follow_redirects,
        )

    @asynccontextmanager
    async def async_stream(
        self,
        method: str,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> typing.AsyncIterator[httpx.Response]:
        """
        Alternative to `httpx.request()` that streams the response body
        instead of loading it into memory at once.

        **Parameters**: See `httpx.request`.

        See also: [Streaming Responses][0]

        [0]: /quickstart#streaming-responses
        """
        request = await self.async_build_request(
            method=method,
            url=url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )
        response = await self.async_send(
            request=request,
            auth=auth,
            follow_redirects=follow_redirects,
            stream=True,
        )
        try:
            yield response
        finally:
            await response.aclose()

    async def async_request(
        self,
        method: str,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault, None] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
        **kwargs,
    ) -> httpx.Response:
        #if not self._async_active:
        #    self._init_clients(_reset_async = True)
        if self._config.debug:
            logger.info(f"Request: {method} {url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Params: {params}")

        return await self.async_client.request(
            method=method,
            url=url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
            **kwargs,
        )
    
    async def async_get(
        self,
        url: httpxType.URLTypes,
        *,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault, None] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
        soup_enabled: typing.Optional[bool] = None,
    ) -> httpx.Response:
        """
        Send a `GET` request.

        **Parameters**: See `httpx.request`.
        """
        response = await self.async_request(
            "GET",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )
        if soup_enabled is True or self._config.soup_enabled is True:
            response = wrap_soup_response(response)
        return response

    async def async_options(
        self,
        url: httpxType.URLTypes,
        *,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send an `OPTIONS` request.

        **Parameters**: See `httpx.request`.
        """
        return await self.async_request(
            "OPTIONS",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    async def async_head(
        self,
        url: httpxType.URLTypes,
        *,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `HEAD` request.

        **Parameters**: See `httpx.request`.
        """
        return await self.async_request(
            "HEAD",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    async def async_post(
        self,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `POST` request.

        **Parameters**: See `httpx.request`.
        """
        return await self.async_request(
            "POST",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    async def async_put(
        self,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `PUT` request.

        **Parameters**: See `httpx.request`.
        """
        return await self.async_request(
            "PUT",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    async def async_patch(
        self,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `PATCH` request.

        **Parameters**: See `httpx.request`.
        """
        return await self.async_request(
            "PATCH",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    async def async_delete(
        self,
        url: httpxType.URLTypes,
        *,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `DELETE` request.

        **Parameters**: See `httpx.request`.
        """
        return await self.async_request(
            "DELETE",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )
    
    """
    Sync Methods
    """
    def send(
        self,
        request: httpx.Request,
        *args,
        stream: bool = False,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault, None] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        """
        Send a request.

        The request is sent as-is, unmodified.

        Typically you'll want to build one with `Client.build_request()`
        so that any client-level configuration is merged into the request,
        but passing an explicit `httpx.Request()` is supported as well.

        See also: [Request instances][0]

        [0]: /advanced/#request-instances
        """
        return self.sync_client.send(
            request,
            *args,
            stream=stream,
            auth=auth,
            follow_redirects=follow_redirects,
        )

    @contextmanager
    def stream(
        self,
        method: str,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> typing.Iterator[httpx.Response]:
        """
        Alternative to `httpx.request()` that streams the response body
        instead of loading it into memory at once.

        **Parameters**: See `httpx.request`.

        See also: [Streaming Responses][0]

        [0]: /quickstart#streaming-responses
        """
        request = self.build_request(
            method=method,
            url=url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )
        response = self.send(
            request=request,
            auth=auth,
            follow_redirects=follow_redirects,
            stream=True,
        )
        try:
            yield response
        finally:
            response.close()

    def request(
        self,
        method: str,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault, None] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
        **kwargs,
    ) -> httpx.Response:
        #if not self._sync_active:
        #    self._init_clients(_reset_sync = True)
        if self._config.debug:
            logger.info(f"Request: {method} {url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Params: {params}")
        return self.sync_client.request(
            method=method,
            url=url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
            **kwargs,
        )
    
    def get(
        self,
        url: httpxType.URLTypes,
        *,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault, None] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
        soup_enabled: typing.Optional[bool] = None,
    ) -> httpx.Response:
        """
        Send a `GET` request.

        **Parameters**: See `httpx.request`.
        """
        response = self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )
        if soup_enabled is True or self._config.soup_enabled is True:
            response = wrap_soup_response(response)
        return response

    def options(
        self,
        url: httpxType.URLTypes,
        *,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send an `OPTIONS` request.

        **Parameters**: See `httpx.request`.
        """
        return self.request(
            "OPTIONS",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    def head(
        self,
        url: httpxType.URLTypes,
        *,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `HEAD` request.

        **Parameters**: See `httpx.request`.
        """
        return self.request(
            "HEAD",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    def post(
        self,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `POST` request.

        **Parameters**: See `httpx.request`.
        """
        return self.request(
            "POST",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    def put(
        self,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `PUT` request.

        **Parameters**: See `httpx.request`.
        """
        return self.request(
            "PUT",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    def patch(
        self,
        url: httpxType.URLTypes,
        *,
        content: typing.Optional[httpxType.RequestContent] = None,
        data: typing.Optional[httpxType.RequestData] = None,
        files: typing.Optional[httpxType.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `PATCH` request.

        **Parameters**: See `httpx.request`.
        """
        return self.request(
            "PATCH",
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    def delete(
        self,
        url: httpxType.URLTypes,
        *,
        params: typing.Optional[httpxType.QueryParamTypes] = None,
        headers: typing.Optional[httpxType.HeaderTypes] = None,
        cookies: typing.Optional[httpxType.CookieTypes] = None,
        auth: typing.Union[httpxType.AuthTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpxType.TimeoutTypes, httpxType.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
    ) -> httpx.Response:
        """
        Send a `DELETE` request.

        **Parameters**: See `httpx.request`.
        """
        return self.request(
            "DELETE",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )

    """
    Startup/Shutdown
    """

    def startup(self) -> None:
        pass

    async def async_startup(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    async def async_shutdown(self) -> None:
        pass

    def close(self) -> None:
        """
        Close transport and proxies.
        """
        self.shutdown()
        if self._sync_active:
            self.sync_client.close()
            self._sync_active = False
            

    async def aclose(self) -> None:
        """
        Close transport and proxies.
        """
        await self.async_shutdown()
        if self._async_active:
            await self.async_client.aclose()
            self._async_active = False

    def __enter__(self):
        self.startup()
        # self.sync_client.__enter__()
        return self

    async def __aenter__(self):
        await self.async_startup()
        # await self.async_client.__aenter__()
        return self
    
    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]] = None,
        exc_value: typing.Optional[BaseException] = None,
        traceback: typing.Optional[httpxType.TracebackType] = None,
    ) -> None:
        self.close()
        if self._sync_active:
            self.sync_client.__exit__(exc_type, exc_value, traceback)
            self._sync_active = False

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]] = None,
        exc_value: typing.Optional[BaseException] = None,
        traceback: typing.Optional[httpxType.TracebackType] = None,
    ) -> None:
        await self.aclose()
        if self._async_active:
            await self.async_client.__aexit__(exc_type, exc_value, traceback)
            self._async_active = False