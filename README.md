# aiohttpx
 A Python Wrapper for httpx that combines the httpx.AsyncClient with the httpx.Client to allow both async and sync requests
 
 **Latest Version**: [![PyPI version](https://badge.fury.io/py/aiohttpx.svg)](https://badge.fury.io/py/aiohttpx)

---

### Installation

```bash
# Install from pypi
pip install --upgrade aiohttpx

# Install from Github
pip install --upgrade git+https://github.com/trisongz/aiohttpx

```

---

## Usage

`aiohttpx` is a wrapper around `httpx` that provides a unified `async` + `sync` interface for making HTTP requests. This is useful for making HTTP requests in both `async` and `sync` codebases. 

Additionally, it includes a `ProxyClient` that can be used for scraping / high volume requests that would otherwise be blocked by the target server by using a rotating proxy pool through `AWS API Gateway`.

```python

import asyncio

import aiohttpx

async def test_requests():
    # Notice it utilizes async context manager but can use sync methods.

    async with aiohttpx.Client() as client:
        # Make an Async GET request
        response = await client.async_get("https://httpbin.org/get")
        print(response.json())

        # Make a Sync GET request
        response = client.get("https://httpbin.org/get")
        print(response.json())
    
    # The same applies with the sync context manager
    with aiohttpx.Client() as client:
        # Make an Async GET request
        response = await client.async_get("https://httpbin.org/get")
        print(response.json())

        # Make a Sync GET request
        response = client.get("https://httpbin.org/get")
        print(response.json())


async def test_proxies():
    # Here we will test the ProxyClient
    # some magic/notes:
    
    # there is a wrapper for BeautifulSoup that is enabled for GET 
    # requests. This can be triggered by passing `soup_enabled=True` 
    # to the request method.
    
    # the ProxyClient will automatically terminate the api gateways upon 
    # exit from the context manager in both sync and async.

    # however if no context manager is used, then the ProxyClient will 
    # need to be manually terminated by calling 
    # `client.shutdown()` | `await client.async_shutdown()`

    # You can choose to perserve the api gateways by passing 
    # `reuse_gateways=True` to the ProxyClient constructor. 
    # This is useful if you want to reuse the same api gateways 
    # for multiple requests.

    # You can also increase the number of gateways per region to 
    # increase the number of concurrent requests. This can be done by 
    # passing `gateways_per_region=10` to the ProxyClient constructor.

    # by default the ProxyClient will use the `us-east-1` region. 
    # You can change this by passing `regions=["us-west-2"]` or 
    # `regions="us"` for all us regions to the ProxyClient constructor.


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
    
    # Upon exiting the context manager, the api gateways will be terminated.


async def run_tests():
    await asyncio.gather(
        test_requests(),
        test_proxies()
    )

asyncio.run(run_tests())

```
