import aiohttpx


c = aiohttpx.Client()


c.headers['test'] = 'hi'

print(c.headers)

c.auth = aiohttpx.BasicAuth(username = 'hi', password = 'hi')

print(c.auth)

print(c.async_client.headers)