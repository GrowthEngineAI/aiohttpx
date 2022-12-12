
## Applies the proxy-gateway to aiohttpx
import httpx
import random
import struct
import socket
import typing

from aiohttpx.configs import settings
from aiohttpx.utils import logger
from aiohttpx.client import Client
from aiohttpx.schemas.proxies import ProxyManager

class ProxyClient(Client):

    def __init__(
        self,
        base_url: str,
        aws_access_key_id: typing.Optional[str] = settings.aws.aws_access_key_id,
        aws_secret_access_key: typing.Optional[str] = settings.aws.aws_secret_access_key,
        regions: typing.Optional[typing.Union[str, typing.List[str]]] = 'default',
        gateways_per_region: typing.Optional[int] = 1,
        reuse_gateways: typing.Optional[bool] = False,
        unique_names: typing.Optional[bool] = False,
        host_header: typing.Optional[str] = None,
        pagination_limit: typing.Optional[int] = 50,
        verbose: bool = False,
        *args,
        **kwargs
    ):

        self._uri = base_url[:-1] if base_url.endswith("/") else base_url
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            raise ValueError("Invalid URL schema")
        
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.host_header = host_header or base_url.split("://", 1)[1].split("/", 1)[0]
        self.verbose = verbose

        self.proxy_manager: ProxyManager = ProxyManager(
            base_url = base_url,
            aws_access_key_id = aws_access_key_id,
            aws_secret_access_key = aws_secret_access_key,
            regions = regions,
            gateways_per_region = gateways_per_region,
            reuse_gateways = reuse_gateways,
            unique_names = unique_names,
            pagination_limit = pagination_limit,
        )
        self._gw_active = False
        super().__init__(*args, **kwargs)
    

    async def async_startup(self) -> None:
        if self._gw_active: return
        await self.proxy_manager.async_build_endpoints()
        self._gw_active = True
        
    async def async_shutdown(self, force: bool = False) -> None:
        if not self._gw_active: return
        await self.proxy_manager.async_clear_apis(force = force)
        self._gw_active = False
    
    def startup(self) -> None:
        if self._gw_active: return
        self.proxy_manager.build_endpoints()
        self._gw_active = True

    def shutdown(self, force: bool = False) -> None:
        if not self._gw_active: return
        self.proxy_manager.clear_apis(force = force)
        self._gw_active = False
    
    async def async_request(
        self,
        method: str,
        url: typing.Union[str, typing.Any],
        *,
        content: typing.Optional[httpx._client.RequestContent] = None,
        data: typing.Optional[httpx._client.RequestData] = None,
        files: typing.Optional[httpx._client.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpx._client.QueryParamTypes] = None,
        headers: typing.Optional[httpx._client.HeaderTypes] = None,
        cookies: typing.Optional[httpx._client.CookieTypes] = None,
        auth: typing.Union[httpx._client.AuthTypes, httpx._client.UseClientDefault, None] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpx._client.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpx._client.TimeoutTypes, httpx._client.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
        region: typing.Optional[str] = None,
        debug: typing.Optional[bool] = False,
    ) -> httpx.Response:
        if not self._gw_active:
            await self.async_startup()
        endpoint = self.proxy_manager.get_randomized_endpoint(region = region)
        try: path = url.split("://", 1)[1].split("/", 1)[1]
        except IndexError: path = ""
        url = f"https://{endpoint}/proxy-stage/{path}"
        if debug or self._config.debug:
            logger.info(f"Sending request to {url}")
        headers = headers or {}
        headers.pop("X-Forwarded-For", None)
        headers["X-Host"] = self.host_header
        headers["X-Forwarded-Header"] = headers.get("X-Forwarded-For") or socket.inet_ntoa(struct.pack(">I", random.randint(1, 0xffffffff)))
        headers["X-User-Agent"] = headers.get("User-Agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        if debug or self._config.debug:
            logger.info(f"Headers: {headers}")
        return await super().async_request(
            method,
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

    """
    Sync Methods
    """
    

    def request(
        self,
        method: str,
        url: typing.Union[str, typing.Any],
        *,
        content: typing.Optional[httpx._client.RequestContent] = None,
        data: typing.Optional[httpx._client.RequestData] = None,
        files: typing.Optional[httpx._client.RequestFiles] = None,
        json: typing.Optional[typing.Any] = None,
        params: typing.Optional[httpx._client.QueryParamTypes] = None,
        headers: typing.Optional[httpx._client.HeaderTypes] = None,
        cookies: typing.Optional[httpx._client.CookieTypes] = None,
        auth: typing.Union[httpx._client.AuthTypes, httpx._client.UseClientDefault, None] = httpx._client.USE_CLIENT_DEFAULT,
        follow_redirects: typing.Union[bool, httpx._client.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        timeout: typing.Union[httpx._client.TimeoutTypes, httpx._client.UseClientDefault] = httpx._client.USE_CLIENT_DEFAULT,
        extensions: typing.Optional[dict] = None,
        region: typing.Optional[str] = None,
        debug: typing.Optional[bool] = False,
    ) -> httpx.Response:
        if not self._gw_active: self.startup()
        endpoint = self.proxy_manager.get_randomized_endpoint(region = region)
        try: path = url.split("://", 1)[1].split("/", 1)[1]
        except IndexError: path = ""
        url = f"https://{endpoint}/proxy-stage/{path}"
        if debug or self._config.debug:
            logger.info(f"Sending request to {url}")
        headers = headers or {}
        headers.pop("X-Forwarded-For", None)
        headers["X-Host"] = self.host_header
        headers["X-Forwarded-Header"] = headers.get("X-Forwarded-For") or socket.inet_ntoa(struct.pack(">I", random.randint(1, 0xffffffff)))
        headers["X-User-Agent"] = headers.get("User-Agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        if debug or self._config.debug:
            logger.info(f"Headers: {headers}")
        return super().request(
            method,
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
