from __future__ import absolute_import

"""
A Submodule for httpx that combines
the httpx.AsyncClient with the httpx.Client
to allow both async and sync requests

Usage:

```python

import aiohttpx

with aiohttpx.Client() as client:
    
    # Make an Async GET request
    response = await client.async_get("https://httpbin.org/get")
    print(response.json())

    # Make a Sync GET request
    response = client.get("https://httpbin.org/get")
    print(response.json())


base_url = "https://www.google.com"

async with aiohttpx.ProxyClient(base_url = base_url) as client:
    # Make an Async GET request
    response = await client.async_get(
        "/search", 
        params = {"q": "httpx"},
        soup_enabled = True
    )
    print(response.soup)
    print(response.soup.title.text)

    # Make a Sync GET request
    response = client.get(
        "/search", 
        params = {"q": "httpx"},
        soup_enabled = True
    )
    print(response.soup)
    print(response.soup.title.text)

```

"""

# import top level classes from httpx
# to allow for easy access
from httpx._api import delete, get, head, options, patch, post, put, request, stream
from httpx._auth import Auth, BasicAuth, DigestAuth
from httpx._client import USE_CLIENT_DEFAULT
from httpx._client import AsyncClient as httpxAsyncClient
from httpx._client import Client as httpxClient

from httpx._config import Limits, Proxy, Timeout, create_ssl_context
from httpx._content import ByteStream
from httpx._exceptions import (
    CloseError,
    ConnectError,
    ConnectTimeout,
    CookieConflict,
    DecodingError,
    HTTPError,
    HTTPStatusError,
    InvalidURL,
    LocalProtocolError,
    NetworkError,
    PoolTimeout,
    ProtocolError,
    ProxyError,
    ReadError,
    ReadTimeout,
    RemoteProtocolError,
    RequestError,
    RequestNotRead,
    ResponseNotRead,
    StreamClosed,
    StreamConsumed,
    StreamError,
    TimeoutException,
    TooManyRedirects,
    TransportError,
    UnsupportedProtocol,
    WriteError,
    WriteTimeout,
)
from httpx._models import Cookies, Headers, Request, Response
from httpx._status_codes import codes
from httpx._types import AsyncByteStream, SyncByteStream
from httpx._urls import URL, QueryParams

from urllib.parse import (
    urlparse, 
    urlunparse, 
    urljoin, 
    urldefrag,
    urlsplit, 
    urlunsplit, 
    urlencode, 
    parse_qs,
    parse_qsl, 
    quote, 
    quote_plus, 
    quote_from_bytes,
    unquote, 
    unquote_plus,
    unquote_to_bytes,
)

from aiohttpx.client import Client, ClientParams

from aiohttpx.schemas.proxies import ProxyManager, ProxyRegion, ProxyEndpoint
from aiohttpx.proxy import ProxyClient


