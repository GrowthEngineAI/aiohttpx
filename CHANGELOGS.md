## aiohttpx Changelogs

- 0.0.7 (2023-01-06)
  - added top level imports of common `urllib` utils

- 0.0.6 (2022-12-21)
  - add additional methods to control `cookies`, `headers`, `params`

- 0.0.5 (2022-12-20)
  - add `setters` in properties for `aiohttpx.Client` to apply across both `async` and `sync` methods. 

- 0.0.4 (2022-12-13) [hotfix]
  - Resolve duplicate `Client` classes in `aiohttpx` module.

- 0.0.3 (2022-12-13)
  - Add top level imports from `httpx` for convenience of accessing `httpx` classes and methods.


- 0.0.2 (2022-12-12)
  - Added properties/methods within `aiohttpx.Client` class to achieve closer parity.
    - `aiohttpx.Client.base_url`
    - `aiohttpx.Client.headers`
    - `aiohttpx.Client.cookies`
    - `aiohttpx.Client.params`
    - `aiohttpx.Client.auth`
    - `aiohttpx.Client.event_hooks`
  
  - Added methods to modify both underlying sync and async `Client` properties from above list
    - `aiohttpx.Client.set_base_url`
    - `aiohttpx.Client.set_headers`
    - `aiohttpx.Client.set_cookies`
    - `aiohttpx.Client.set_params`
    - `aiohttpx.Client.set_auth`
    - `aiohttpx.Client.set_event_hooks`


- 0.0.1 (2022-12-12)
    - Initial release.