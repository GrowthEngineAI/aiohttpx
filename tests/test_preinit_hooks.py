
import asyncio
import aiohttpx
from aiohttpx.utils import logger

def sync_init_hook(client: aiohttpx.Client, **kwargs):
    """
    Sync init hook
    """
    logger.info('sync init hook')
    client.headers.update(
        {'sync-header1': 'test-headers'}
    )
    return client

async def async_init_hook(client: aiohttpx.Client, **kwargs):
    """
    Async init hook
    """
    logger.info('async init hook')
    client.headers.update(
        {'async-header1': 'test-headers'}
    )
    return client

def sync_init_hook_kwargs(client: aiohttpx.Client, value: str = None, **kwargs):
    """
    Sync init hook
    """
    logger.info(f'sync init hook with value = {value}, kwargs = {kwargs}')
    client.headers.update(
        {'sync-header2': value}
    )
    return client

async def async_init_hook_kwargs(client: aiohttpx.Client, value: str = None, **kwargs):
    """
    Async init hook
    """
    logger.info(f'async init hook with value = {value}, kwargs = {kwargs}')
    client.headers.update(
        {'async-header2': value}
    )
    return client

async def test_client():

    client = aiohttpx.Client(
        base_url='https://httpbin.org',
        init_hooks=[
            async_init_hook,
            sync_init_hook,
            (async_init_hook_kwargs, {'value': 'async-value'}),
            (sync_init_hook_kwargs, {'value': 'sync-value'}),
        ]
    )
    await client.async_get('/get')
    logger.info(f'client.headers = {client.headers}')

if __name__ == '__main__':
    asyncio.run(test_client())