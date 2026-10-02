# WebSockets - FastAPI

Source: https://fastapi.tiangolo.com/reference/websockets/

# WebSockets[¶](https://fastapi.tiangolo.com/reference/websockets/#websockets "Permanent link")
When defining WebSockets, you normally declare a parameter of type `WebSocket` and with it you can read data from the client and send data to it.
Read more about it in the [FastAPI docs for WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
It is provided directly by Starlette, but you can import it from `fastapi`:

```
from fastapi import WebSocket

```

Tip
When you want to define dependencies that should be compatible with both HTTP and WebSockets, you can define a parameter that takes an `HTTPConnection` instead of a `Request` or a `WebSocket`.
##  `` fastapi.WebSocket [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket "Permanent link")

```
WebSocket(scope, receive, send)

```

Bases: `HTTPConnection[](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.requests.HTTPConnection</span> \(<code>starlette.requests.HTTPConnection</code>\)")[StateT]`
Source code in `starlette/websockets.py`

```
def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
    super().__init__(scope)
    assert scope["type"] == "websocket"
    self._receive = receive
    self._send = send
    self.client_state = WebSocketState.CONNECTING
    self.application_state = WebSocketState.CONNECTING

```

###  `` scope `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.scope "Permanent link")

```
scope = scope

```

###  `` app `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.app "Permanent link")

```
app

```

###  `` url `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.url "Permanent link")

```
url

```

###  `` base_url `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.base_url "Permanent link")

```
base_url

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.headers "Permanent link")

```
headers

```

###  `` query_params `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.query_params "Permanent link")

```
query_params

```

###  `` path_params `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.path_params "Permanent link")

```
path_params

```

###  `` cookies `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.cookies "Permanent link")

```
cookies

```

###  `` client `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.client "Permanent link")

```
client

```

###  `` state `property` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.state "Permanent link")

```
state

```

###  `` client_state `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.client_state "Permanent link")

```
client_state = CONNECTING[](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketState.CONNECTING "<code class="doc-symbol doc-symbol-heading doc-symbol-attribute"></code>            <span class="doc doc-object-name doc-attribute-name">CONNECTING</span>


  <span class="doc doc-labels">
      <small class="doc doc-label doc-label-class-attribute"><code>class-attribute</code></small>
      <small class="doc doc-label doc-label-instance-attribute"><code>instance-attribute</code></small>
  </span> \(<code>starlette.websockets.WebSocketState.CONNECTING</code>\)")

```

###  `` application_state `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.application_state "Permanent link")

```
application_state = CONNECTING[](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketState.CONNECTING "<code class="doc-symbol doc-symbol-heading doc-symbol-attribute"></code>            <span class="doc doc-object-name doc-attribute-name">CONNECTING</span>


  <span class="doc doc-labels">
      <small class="doc doc-label doc-label-class-attribute"><code>class-attribute</code></small>
      <small class="doc doc-label doc-label-instance-attribute"><code>instance-attribute</code></small>
  </span> \(<code>starlette.websockets.WebSocketState.CONNECTING</code>\)")

```

###  `` url_for [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.url_for "Permanent link")

```
url_for(name, /, **path_params)

```

Source code in `starlette/requests.py`

```
def url_for(self, name: str, /, **path_params: Any) -> URL:
    url_path_provider: Router | Starlette | None = self.scope.get("router") or self.scope.get("app")
    if url_path_provider is None:
        raise RuntimeError("The `url_for` method can only be used inside a Starlette application or with a router.")
    url_path = url_path_provider.url_path_for(name, **path_params)
    return url_path.make_absolute_url(base_url=self.base_url)

```

###  `` receive `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.receive "Permanent link")

```
receive()

```

Receive ASGI websocket messages, ensuring valid state transitions.
Source code in `starlette/websockets.py`

```
async def receive(self) -> Message:
    """
    Receive ASGI websocket messages, ensuring valid state transitions.
    """
    if self.client_state == WebSocketState.CONNECTING:
        message = await self._receive()
        message_type = message["type"]
        if message_type != "websocket.connect":
            raise RuntimeError(f'Expected ASGI message "websocket.connect", but got {message_type!r}')
        self.client_state = WebSocketState.CONNECTED
        return message
    elif self.client_state == WebSocketState.CONNECTED:
        message = await self._receive()
        message_type = message["type"]
        if message_type not in {"websocket.receive", "websocket.disconnect"}:
            raise RuntimeError(
                f'Expected ASGI message "websocket.receive" or "websocket.disconnect", but got {message_type!r}'
            )
        if message_type == "websocket.disconnect":
            self.client_state = WebSocketState.DISCONNECTED
        return message
    else:
        raise WebSocketDisconnected('Cannot call "receive" once a disconnect message has been received.')

```

###  `` send `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.send "Permanent link")

```
send(message)

```

Send ASGI websocket messages, ensuring valid state transitions.
Source code in `starlette/websockets.py`

```
async def send(self, message: Message) -> None:
    """
    Send ASGI websocket messages, ensuring valid state transitions.
    """
    if self.application_state == WebSocketState.CONNECTING:
        message_type = message["type"]
        if message_type not in {"websocket.accept", "websocket.close", "websocket.http.response.start"}:
            raise RuntimeError(
                'Expected ASGI message "websocket.accept", "websocket.close" or "websocket.http.response.start", '
                f"but got {message_type!r}"
            )
        if message_type == "websocket.close":
            self.application_state = WebSocketState.DISCONNECTED
        elif message_type == "websocket.http.response.start":
            self.application_state = WebSocketState.RESPONSE
        else:
            self.application_state = WebSocketState.CONNECTED
        await self._send(message)
    elif self.application_state == WebSocketState.CONNECTED:
        message_type = message["type"]
        if message_type not in {"websocket.send", "websocket.close"}:
            raise RuntimeError(
                f'Expected ASGI message "websocket.send" or "websocket.close", but got {message_type!r}'
            )
        if message_type == "websocket.close":
            self.application_state = WebSocketState.DISCONNECTED
        try:
            await self._send(message)
        except OSError:
            self.application_state = WebSocketState.DISCONNECTED
            raise WebSocketDisconnect(code=1006)
    elif self.application_state == WebSocketState.RESPONSE:
        message_type = message["type"]
        if message_type != "websocket.http.response.body":
            raise RuntimeError(f'Expected ASGI message "websocket.http.response.body", but got {message_type!r}')
        if not message.get("more_body", False):
            self.application_state = WebSocketState.DISCONNECTED
        await self._send(message)
    else:
        raise WebSocketDisconnected('Cannot call "send" once a close message has been sent.')

```

###  `` accept `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.accept "Permanent link")

```
accept(subprotocol=None, headers=None)

```

Source code in `starlette/websockets.py`

```
async def accept(
    self,
    subprotocol: str | None = None,
    headers: Iterable[tuple[bytes, bytes]] | None = None,
) -> None:
    headers = headers or []

    if self.client_state == WebSocketState.CONNECTING:  # pragma: no branch
        # If we haven't yet seen the 'connect' message, then wait for it first.
        await self.receive()
    await self.send({"type": "websocket.accept", "subprotocol": subprotocol, "headers": headers})

```

###  `` receive_text `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.receive_text "Permanent link")

```
receive_text()

```

Source code in `starlette/websockets.py`

```
async def receive_text(self) -> str:
    if self.application_state != WebSocketState.CONNECTED:
        raise WebSocketDisconnected('WebSocket is not connected. Need to call "accept" first.')
    message = await self.receive()
    self._raise_on_disconnect(message)
    return cast(str, message["text"])

```

###  `` receive_bytes `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.receive_bytes "Permanent link")

```
receive_bytes()

```

Source code in `starlette/websockets.py`

```
async def receive_bytes(self) -> bytes:
    if self.application_state != WebSocketState.CONNECTED:
        raise WebSocketDisconnected('WebSocket is not connected. Need to call "accept" first.')
    message = await self.receive()
    self._raise_on_disconnect(message)
    return cast(bytes, message["bytes"])

```

###  `` receive_json `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.receive_json "Permanent link")

```
receive_json(mode='text')

```

Source code in `starlette/websockets.py`

```
async def receive_json(self, mode: str = "text") -> Any:
    if mode not in {"text", "binary"}:
        raise RuntimeError('The "mode" argument should be "text" or "binary".')
    if self.application_state != WebSocketState.CONNECTED:
        raise WebSocketDisconnected('WebSocket is not connected. Need to call "accept" first.')
    message = await self.receive()
    self._raise_on_disconnect(message)

    if mode == "text":
        text = message["text"]
    else:
        text = message["bytes"].decode("utf-8")
    return json.loads(text)

```

###  `` iter_text `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.iter_text "Permanent link")

```
iter_text()

```

Source code in `starlette/websockets.py`

```
async def iter_text(self) -> AsyncIterator[str]:
    try:
        while True:
            yield await self.receive_text()
    except WebSocketDisconnect:
        pass

```

###  `` iter_bytes `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.iter_bytes "Permanent link")

```
iter_bytes()

```

Source code in `starlette/websockets.py`

```
async def iter_bytes(self) -> AsyncIterator[bytes]:
    try:
        while True:
            yield await self.receive_bytes()
    except WebSocketDisconnect:
        pass

```

###  `` iter_json `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.iter_json "Permanent link")

```
iter_json()

```

Source code in `starlette/websockets.py`

```
async def iter_json(self) -> AsyncIterator[Any]:
    try:
        while True:
            yield await self.receive_json()
    except WebSocketDisconnect:
        pass

```

###  `` send_text `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.send_text "Permanent link")

```
send_text(data)

```

Source code in `starlette/websockets.py`

```
async def send_text(self, data: str) -> None:
    await self.send({"type": "websocket.send", "text": data})

```

###  `` send_bytes `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.send_bytes "Permanent link")

```
send_bytes(data)

```

Source code in `starlette/websockets.py`

```
async def send_bytes(self, data: bytes) -> None:
    await self.send({"type": "websocket.send", "bytes": data})

```

###  `` send_json `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.send_json "Permanent link")

```
send_json(data, mode='text')

```

Source code in `starlette/websockets.py`

```
async def send_json(self, data: Any, mode: str = "text") -> None:
    if mode not in {"text", "binary"}:
        raise RuntimeError('The "mode" argument should be "text" or "binary".')
    text = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    if mode == "text":
        await self.send({"type": "websocket.send", "text": text})
    else:
        await self.send({"type": "websocket.send", "bytes": text.encode("utf-8")})

```

###  `` close `async` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.WebSocket.close "Permanent link")

```
close(code=1000, reason=None)

```

Source code in `starlette/websockets.py`

```
async def close(self, code: int = 1000, reason: str | None = None) -> None:
    await self.send({"type": "websocket.close", "code": code, "reason": reason or ""})

```

## WebSockets - additional classes[¶](https://fastapi.tiangolo.com/reference/websockets/#websockets-additional-classes "Permanent link")
Additional classes for handling WebSockets.
Provided directly by Starlette, but you can import them from `fastapi`:

```
from fastapi.websockets import WebSocketDisconnect, WebSocketState

```

##  `` fastapi.websockets.WebSocketDisconnect [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketDisconnect "Permanent link")

```
WebSocketDisconnect(code=1000, reason=None)

```

Bases: `Exception`
Source code in `starlette/websockets.py`

```
def __init__(self, code: int = 1000, reason: str | None = None) -> None:
    self.code = code
    self.reason = reason or ""

```

###  `` code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketDisconnect.code "Permanent link")

```
code = code

```

###  `` reason `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketDisconnect.reason "Permanent link")

```
reason = reason or ''

```

When a client disconnects, a `WebSocketDisconnect` exception is raised, you can catch it.
You can import it directly from `fastapi`:

```
from fastapi import WebSocketDisconnect

```

Read more about it in the [FastAPI docs for WebSockets](https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients)
##  `` fastapi.websockets.WebSocketState [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketState "Permanent link")
Bases: `Enum`
###  `` CONNECTING `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketState.CONNECTING "Permanent link")

```
CONNECTING = 0

```

###  `` CONNECTED `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketState.CONNECTED "Permanent link")

```
CONNECTED = 1

```

###  `` DISCONNECTED `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketState.DISCONNECTED "Permanent link")

```
DISCONNECTED = 2

```

###  `` RESPONSE `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/websockets/#fastapi.websockets.WebSocketState.RESPONSE "Permanent link")

```
RESPONSE = 3

```

`WebSocketState` is an enumeration of the possible states of a WebSocket connection.
