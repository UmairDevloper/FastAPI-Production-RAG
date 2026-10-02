# Test Client - TestClient - FastAPI

Source: https://fastapi.tiangolo.com/reference/testclient/

# Test Client - `TestClient`[¶](https://fastapi.tiangolo.com/reference/testclient/#test-client-testclient "Permanent link")
You can use the `TestClient` class to test FastAPI applications without creating an actual HTTP and socket connection, just communicating directly with the FastAPI code.
Read more about it in the [FastAPI docs for Testing](https://fastapi.tiangolo.com/tutorial/testing/).
You can import it directly from `fastapi.testclient`:

```
from fastapi.testclient import TestClient

```

##  `` fastapi.testclient.TestClient [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient "Permanent link")

```
TestClient(
    app,
    base_url="http://testserver",
    raise_server_exceptions=True,
    root_path="",
    backend="asyncio",
    backend_options=None,
    cookies=None,
    headers=None,
    follow_redirects=True,
    client=("testclient", 50000),
)

```

Bases: `Client`
Source code in `starlette/testclient.py`

```
def __init__(
    self,
    app: ASGIApp,
    base_url: str = "http://testserver",
    raise_server_exceptions: bool = True,
    root_path: str = "",
    backend: Literal["asyncio", "trio"] = "asyncio",
    backend_options: dict[str, Any] | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    headers: dict[str, str] | None = None,
    follow_redirects: bool = True,
    client: tuple[str, int] = ("testclient", 50000),
) -> None:
    self.async_backend = _AsyncBackend(backend=backend, backend_options=backend_options or {})
    if _is_asgi3(app):
        asgi_app = app
    else:
        app = cast(ASGI2App, app)  # type: ignore[assignment]
        asgi_app = _WrapASGI2(app)  # type: ignore[arg-type]
    self.app = asgi_app
    self.app_state: dict[str, Any] = {}
    transport = _TestClientTransport(
        self.app,
        portal_factory=self._portal_factory,
        raise_server_exceptions=raise_server_exceptions,
        root_path=root_path,
        app_state=self.app_state,
        client=client,
    )
    if headers is None:
        headers = {}
    headers.setdefault("user-agent", "testclient")
    super().__init__(
        base_url=base_url,
        headers=headers,
        transport=transport,
        follow_redirects=follow_redirects,
        cookies=cookies,
    )

```

###  `` headers `property` `writable` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.headers "Permanent link")

```
headers

```

HTTP headers to include when sending requests.
###  `` follow_redirects `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.follow_redirects "Permanent link")

```
follow_redirects = follow_redirects

```

###  `` max_redirects `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.max_redirects "Permanent link")

```
max_redirects = max_redirects

```

###  `` is_closed `property` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.is_closed "Permanent link")

```
is_closed

```

Check if the client being closed
###  `` trust_env `property` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.trust_env "Permanent link")

```
trust_env

```

###  `` timeout `property` `writable` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.timeout "Permanent link")

```
timeout

```

###  `` event_hooks `property` `writable` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.event_hooks "Permanent link")

```
event_hooks

```

###  `` auth `property` `writable` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.auth "Permanent link")

```
auth

```

Authentication class used when none is passed at the request-level.
See also [Authentication](https://fastapi.tiangolo.com/quickstart/#authentication).
###  `` base_url `property` `writable` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.base_url "Permanent link")

```
base_url

```

Base URL to use when sending requests with relative URLs.
###  `` cookies `property` `writable` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.cookies "Permanent link")

```
cookies

```

Cookie values to include when sending requests.
###  `` params `property` `writable` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.params "Permanent link")

```
params

```

Query parameters to include in the URL when sending requests.
###  `` task `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.task "Permanent link")

```
task

```

###  `` portal `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.portal "Permanent link")

```
portal = None

```

###  `` async_backend `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.async_backend "Permanent link")

```
async_backend = _AsyncBackend(
    backend=backend, backend_options=backend_options or {}
)

```

###  `` app `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.app "Permanent link")

```
app = asgi_app

```

###  `` app_state `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.app_state "Permanent link")

```
app_state = {}

```

###  `` build_request [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.build_request "Permanent link")

```
build_request(
    method,
    url,
    *,
    content=None,
    data=None,
    files=None,
    json=None,
    params=None,
    headers=None,
    cookies=None,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Build and return a request instance.
  * The `params`, `headers` and `cookies` arguments are merged with any values set on the client.
  * The `url` argument is merged with any `base_url` set on the client.


See also: [Request instances](https://fastapi.tiangolo.com/advanced/clients/#request-instances)
Source code in `httpx/_client.py`

```
def build_request(
    self,
    method: str,
    url: URL | str,
    *,
    content: RequestContent | None = None,
    data: RequestData | None = None,
    files: RequestFiles | None = None,
    json: typing.Any | None = None,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> Request:
    """
    Build and return a request instance.

    * The `params`, `headers` and `cookies` arguments
    are merged with any values set on the client.
    * The `url` argument is merged with any `base_url` set on the client.

    See also: [Request instances][0]

    [0]: /advanced/clients/#request-instances
    """
    url = self._merge_url(url)
    headers = self._merge_headers(headers)
    cookies = self._merge_cookies(cookies)
    params = self._merge_queryparams(params)
    extensions = {} if extensions is None else extensions
    if "timeout" not in extensions:
        timeout = (
            self.timeout
            if isinstance(timeout, UseClientDefault)
            else Timeout(timeout)
        )
        extensions = dict(**extensions, timeout=timeout.as_dict())
    return Request(
        method,
        url,
        content=content,
        data=data,
        files=files,
        json=json,
        params=params,
        headers=headers,
        cookies=cookies,
        extensions=extensions,
    )

```

###  `` stream [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.stream "Permanent link")

```
stream(
    method,
    url,
    *,
    content=None,
    data=None,
    files=None,
    json=None,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Alternative to `httpx.request()` that streams the response body instead of loading it into memory at once.
**Parameters** : See `httpx.request`.
See also: [Streaming Responses](https://fastapi.tiangolo.com/quickstart#streaming-responses)
Source code in `httpx/_client.py`

```
@contextmanager
def stream(
    self,
    method: str,
    url: URL | str,
    *,
    content: RequestContent | None = None,
    data: RequestData | None = None,
    files: RequestFiles | None = None,
    json: typing.Any | None = None,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> typing.Iterator[Response]:
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

```

###  `` send [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.send "Permanent link")

```
send(
    request,
    *,
    stream=False,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT
)

```

Send a request.
The request is sent as-is, unmodified.
Typically you'll want to build one with `Client.build_request()` so that any client-level configuration is merged into the request, but passing an explicit `httpx.Request()` is supported as well.
See also: [Request instances](https://fastapi.tiangolo.com/advanced/clients/#request-instances)
Source code in `httpx/_client.py`

```
def send(
    self,
    request: Request,
    *,
    stream: bool = False,
    auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
) -> Response:
    """
    Send a request.

    The request is sent as-is, unmodified.

    Typically you'll want to build one with `Client.build_request()`
    so that any client-level configuration is merged into the request,
    but passing an explicit `httpx.Request()` is supported as well.

    See also: [Request instances][0]

    [0]: /advanced/clients/#request-instances
    """
    if self._state == ClientState.CLOSED:
        raise RuntimeError("Cannot send a request, as the client has been closed.")

    self._state = ClientState.OPENED
    follow_redirects = (
        self.follow_redirects
        if isinstance(follow_redirects, UseClientDefault)
        else follow_redirects
    )

    self._set_timeout(request)

    auth = self._build_request_auth(request, auth)

    response = self._send_handling_auth(
        request,
        auth=auth,
        follow_redirects=follow_redirects,
        history=[],
    )
    try:
        if not stream:
            response.read()

        return response

    except BaseException as exc:
        response.close()
        raise exc

```

###  `` get [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.get "Permanent link")

```
get(
    url,
    *,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Send a `GET` request.
**Parameters** : See `httpx.request`.
Source code in `httpx/_client.py`

```
def get(
    self,
    url: URL | str,
    *,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    auth: AuthTypes | UseClientDefault | None = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> Response:
    """
    Send a `GET` request.

    **Parameters**: See `httpx.request`.
    """
    return self.request(
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

```

###  `` options [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.options "Permanent link")

```
options(
    url,
    *,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Send an `OPTIONS` request.
**Parameters** : See `httpx.request`.
Source code in `httpx/_client.py`

```
def options(
    self,
    url: URL | str,
    *,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> Response:
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

```

###  `` head [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.head "Permanent link")

```
head(
    url,
    *,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Send a `HEAD` request.
**Parameters** : See `httpx.request`.
Source code in `httpx/_client.py`

```
def head(
    self,
    url: URL | str,
    *,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> Response:
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

```

###  `` post [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.post "Permanent link")

```
post(
    url,
    *,
    content=None,
    data=None,
    files=None,
    json=None,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Send a `POST` request.
**Parameters** : See `httpx.request`.
Source code in `httpx/_client.py`

```
def post(
    self,
    url: URL | str,
    *,
    content: RequestContent | None = None,
    data: RequestData | None = None,
    files: RequestFiles | None = None,
    json: typing.Any | None = None,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> Response:
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

```

###  `` put [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.put "Permanent link")

```
put(
    url,
    *,
    content=None,
    data=None,
    files=None,
    json=None,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Send a `PUT` request.
**Parameters** : See `httpx.request`.
Source code in `httpx/_client.py`

```
def put(
    self,
    url: URL | str,
    *,
    content: RequestContent | None = None,
    data: RequestData | None = None,
    files: RequestFiles | None = None,
    json: typing.Any | None = None,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> Response:
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

```

###  `` patch [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.patch "Permanent link")

```
patch(
    url,
    *,
    content=None,
    data=None,
    files=None,
    json=None,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Send a `PATCH` request.
**Parameters** : See `httpx.request`.
Source code in `httpx/_client.py`

```
def patch(
    self,
    url: URL | str,
    *,
    content: RequestContent | None = None,
    data: RequestData | None = None,
    files: RequestFiles | None = None,
    json: typing.Any | None = None,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> Response:
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

```

###  `` delete [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.delete "Permanent link")

```
delete(
    url,
    *,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Send a `DELETE` request.
**Parameters** : See `httpx.request`.
Source code in `httpx/_client.py`

```
def delete(
    self,
    url: URL | str,
    *,
    params: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    cookies: CookieTypes | None = None,
    auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
    timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
    extensions: RequestExtensions | None = None,
) -> Response:
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

```

###  `` close [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.close "Permanent link")

```
close()

```

Close transport and proxies.
Source code in `httpx/_client.py`

```
def close(self) -> None:
    """
    Close transport and proxies.
    """
    if self._state != ClientState.CLOSED:
        self._state = ClientState.CLOSED

        self._transport.close()
        for transport in self._mounts.values():
            if transport is not None:
                transport.close()

```

###  `` request [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.request "Permanent link")

```
request(
    method,
    url,
    *,
    content=None,
    data=None,
    files=None,
    json=None,
    params=None,
    headers=None,
    cookies=None,
    auth=USE_CLIENT_DEFAULT,
    follow_redirects=USE_CLIENT_DEFAULT,
    timeout=USE_CLIENT_DEFAULT,
    extensions=None
)

```

Source code in `starlette/testclient.py`

```
def request(  # type: ignore[override]
    self,
    method: str,
    url: httpx._types.URLTypes,
    *,
    content: httpx._types.RequestContent | None = None,
    data: _RequestData | None = None,
    files: httpx._types.RequestFiles | None = None,
    json: Any = None,
    params: httpx._types.QueryParamTypes | None = None,
    headers: httpx._types.HeaderTypes | None = None,
    cookies: httpx._types.CookieTypes | None = None,
    auth: httpx._types.AuthTypes | httpx._client.UseClientDefault = httpx._client.USE_CLIENT_DEFAULT,
    follow_redirects: bool | httpx._client.UseClientDefault = httpx._client.USE_CLIENT_DEFAULT,
    timeout: httpx._types.TimeoutTypes | httpx._client.UseClientDefault = httpx._client.USE_CLIENT_DEFAULT,
    extensions: dict[str, Any] | None = None,
) -> httpx.Response:
    if timeout is not httpx.USE_CLIENT_DEFAULT:
        warnings.warn(
            "You should not use the 'timeout' argument with the TestClient. "
            "See https://github.com/Kludex/starlette/issues/1108 for more information.",
            StarletteDeprecationWarning,
            stacklevel=2,
        )
    url = self._merge_url(url)
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

```

###  `` websocket_connect [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.websocket_connect "Permanent link")

```
websocket_connect(url, subprotocols=None, **kwargs)

```

Source code in `starlette/testclient.py`

```
def websocket_connect(
    self,
    url: str,
    subprotocols: Sequence[str] | None = None,
    **kwargs: Any,
) -> WebSocketTestSession:
    url = urljoin("ws://testserver", url)
    headers = kwargs.get("headers", {})
    headers.setdefault("connection", "upgrade")
    headers.setdefault("sec-websocket-key", "testserver==")
    headers.setdefault("sec-websocket-version", "13")
    if subprotocols is not None:
        headers.setdefault("sec-websocket-protocol", ", ".join(subprotocols))
    kwargs["headers"] = headers
    try:
        super().request("GET", url, **kwargs)
    except _Upgrade as exc:
        session = exc.session
    else:
        raise RuntimeError("Expected WebSocket upgrade")  # pragma: no cover

    return session

```

###  `` lifespan `async` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.lifespan "Permanent link")

```
lifespan()

```

Source code in `starlette/testclient.py`

```
async def lifespan(self) -> None:
    scope = {"type": "lifespan", "state": self.app_state}
    try:
        await self.app(scope, self.stream_receive.receive, self.stream_send.send)
    finally:
        await self.stream_send.send(None)

```

###  `` wait_startup `async` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.wait_startup "Permanent link")

```
wait_startup()

```

Source code in `starlette/testclient.py`

```
async def wait_startup(self) -> None:
    await self.stream_receive.send({"type": "lifespan.startup"})

    async def receive() -> Any:
        message = await self.stream_send.receive()
        if message is None:
            self.task.result()
        return message

    message = await receive()
    assert message["type"] in (
        "lifespan.startup.complete",
        "lifespan.startup.failed",
    )
    if message["type"] == "lifespan.startup.failed":
        await receive()

```

###  `` wait_shutdown `async` [¶](https://fastapi.tiangolo.com/reference/testclient/#fastapi.testclient.TestClient.wait_shutdown "Permanent link")

```
wait_shutdown()

```

Source code in `starlette/testclient.py`

```
async def wait_shutdown(self) -> None:
    async def receive() -> Any:
        message = await self.stream_send.receive()
        if message is None:
            self.task.result()
        return message

    await self.stream_receive.send({"type": "lifespan.shutdown"})
    message = await receive()
    assert message["type"] in (
        "lifespan.shutdown.complete",
        "lifespan.shutdown.failed",
    )
    if message["type"] == "lifespan.shutdown.failed":
        await receive()

```

