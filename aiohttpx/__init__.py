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


from aiohttpx.client import Client, ClientParams

from aiohttpx.schemas.proxies import ProxyManager, ProxyRegion, ProxyEndpoint
from aiohttpx.proxy import ProxyClient


