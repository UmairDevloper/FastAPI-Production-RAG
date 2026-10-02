# Server-Sent Events - EventSourceResponse and ServerSentEvent - FastAPI

Source: https://fastapi.tiangolo.com/reference/sse/

# Server-Sent Events - `EventSourceResponse` and `ServerSentEvent`[¶](https://fastapi.tiangolo.com/reference/sse/#server-sent-events-eventsourceresponse-and-serversentevent "Permanent link")
To stream Server-Sent Events (SSE), use `yield` in your _path operation function_ and set `response_class=EventSourceResponse`.
If you need to set SSE fields like `event`, `id`, `retry`, or `comment`, you can `yield` `ServerSentEvent` objects instead of plain data.
Read more about it in the [FastAPI docs for Server-Sent Events (SSE)](https://fastapi.tiangolo.com/tutorial/server-sent-events/).
You can import them directly from `fastapi.sse`:

```
from fastapi.sse import EventSourceResponse, ServerSentEvent

```

##  `` fastapi.sse.EventSourceResponse [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse "Permanent link")

```
EventSourceResponse(
    content,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Bases: `StreamingResponse[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.StreamingResponse</span> \(<code>starlette.responses.StreamingResponse</code>\)")`
Streaming response with `text/event-stream` media type.
Use as `response_class=EventSourceResponse` on a _path operation_ that uses `yield` to enable Server Sent Events (SSE) responses.
Works with **any HTTP method** (`GET`, `POST`, etc.), which makes it compatible with protocols like MCP that stream SSE over `POST`.
The actual encoding logic lives in the FastAPI routing layer. This class serves mainly as a marker and sets the correct `Content-Type`.
Source code in `starlette/responses.py`

```
def __init__(
    self,
    content: ContentStream,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> None:
    if isinstance(content, AsyncIterable):
        self.body_iterator = content
    else:
        self.body_iterator = iterate_in_threadpool(content)
    self.status_code = status_code
    self.media_type = self.media_type if media_type is None else media_type
    self.background = background
    self.init_headers(headers)

```

###  `` media_type `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.media_type "Permanent link")

```
media_type = 'text/event-stream'

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.background "Permanent link")

```
background = background

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.body "Permanent link")

```
body = render(content)

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.headers "Permanent link")

```
headers

```

###  `` body_iterator `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.body_iterator "Permanent link")

```
body_iterator

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.render "Permanent link")

```
render(content)

```

Source code in `starlette/responses.py`

```
def render(self, content: Any) -> bytes | memoryview:
    if content is None:
        return b""
    if isinstance(content, bytes | memoryview):
        return content
    return content.encode(self.charset)  # type: ignore

```

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.init_headers "Permanent link")

```
init_headers(headers=None)

```

Source code in `starlette/responses.py`

```
def init_headers(self, headers: Mapping[str, str] | None = None) -> None:
    if headers is None:
        raw_headers: list[tuple[bytes, bytes]] = []
        populate_content_length = True
        populate_content_type = True
    else:
        raw_headers = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()]
        keys = [h[0] for h in raw_headers]
        populate_content_length = b"content-length" not in keys
        populate_content_type = b"content-type" not in keys

    body = getattr(self, "body", None)
    if (
        body is not None
        and populate_content_length
        and not (self.status_code < 200 or self.status_code in (204, 304))
    ):
        content_length = str(len(body))
        raw_headers.append((b"content-length", content_length.encode("latin-1")))

    content_type = self.media_type
    if content_type is not None and populate_content_type:
        if content_type.startswith("text/") and "charset=" not in content_type.lower():
            content_type += "; charset=" + self.charset
        raw_headers.append((b"content-type", content_type.encode("latin-1")))

    self.raw_headers = raw_headers

```

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.set_cookie "Permanent link")

```
set_cookie(
    key,
    value="",
    max_age=None,
    expires=None,
    path="/",
    domain=None,
    secure=False,
    httponly=False,
    samesite="lax",
    partitioned=False,
)

```

Source code in `starlette/responses.py`

```
def set_cookie(
    self,
    key: str,
    value: str = "",
    max_age: int | None = None,
    expires: datetime | str | int | None = None,
    path: str | None = "/",
    domain: str | None = None,
    secure: bool = False,
    httponly: bool = False,
    samesite: Literal["lax", "strict", "none"] | None = "lax",
    partitioned: bool = False,
) -> None:
    cookie: http.cookies.BaseCookie[str] = http.cookies.SimpleCookie()
    cookie[key] = value
    if max_age is not None:
        cookie[key]["max-age"] = max_age
    if expires is not None:
        if isinstance(expires, datetime):
            cookie[key]["expires"] = format_datetime(expires, usegmt=True)
        else:
            cookie[key]["expires"] = expires
    if path is not None:
        cookie[key]["path"] = path
    if domain is not None:
        cookie[key]["domain"] = domain
    if secure:
        cookie[key]["secure"] = True
    if httponly:
        cookie[key]["httponly"] = True
    if samesite is not None:
        assert samesite.lower() in [
            "strict",
            "lax",
            "none",
        ], "samesite must be either 'strict', 'lax' or 'none'"
        cookie[key]["samesite"] = samesite
    if partitioned:
        if sys.version_info < (3, 14):
            raise ValueError("Partitioned cookies are only supported in Python 3.14 and above.")  # pragma: no cover
        cookie[key]["partitioned"] = True  # pragma: no cover

    cookie_val = cookie.output(header="").strip()
    self.raw_headers.append((b"set-cookie", cookie_val.encode("latin-1")))

```

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.delete_cookie "Permanent link")

```
delete_cookie(
    key,
    path="/",
    domain=None,
    secure=False,
    httponly=False,
    samesite="lax",
    partitioned=False,
)

```

Source code in `starlette/responses.py`

```
def delete_cookie(
    self,
    key: str,
    path: str = "/",
    domain: str | None = None,
    secure: bool = False,
    httponly: bool = False,
    samesite: Literal["lax", "strict", "none"] | None = "lax",
    partitioned: bool = False,
) -> None:
    self.set_cookie(
        key,
        max_age=0,
        expires=0,
        path=path,
        domain=domain,
        secure=secure,
        httponly=httponly,
        samesite=samesite,
        partitioned=partitioned,
    )

```

###  `` listen_for_disconnect `async` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.listen_for_disconnect "Permanent link")

```
listen_for_disconnect(receive)

```

Source code in `starlette/responses.py`

```
async def listen_for_disconnect(self, receive: Receive) -> None:
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            break

```

###  `` stream_response `async` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.EventSourceResponse.stream_response "Permanent link")

```
stream_response(send)

```

Source code in `starlette/responses.py`

```
async def stream_response(self, send: Send) -> None:
    await send({"type": "http.response.start", "status": self.status_code, "headers": self.raw_headers})
    async for chunk in self.body_iterator:
        if not isinstance(chunk, bytes | memoryview):
            chunk = chunk.encode(self.charset)
        await send({"type": "http.response.body", "body": chunk, "more_body": True})

    await send({"type": "http.response.body", "body": b"", "more_body": False})

```

##  `` fastapi.sse.ServerSentEvent [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.ServerSentEvent "Permanent link")
Bases: `BaseModel`
Represents a single Server-Sent Event.
When `yield`ed from a _path operation function_ that uses `response_class=EventSourceResponse`, each `ServerSentEvent` is encoded into the [SSE wire format](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream) (`text/event-stream`).
If you yield a plain object (dict, Pydantic model, etc.) instead, it is automatically JSON-encoded and sent as the `data:` field.
All `data` values **including plain strings** are JSON-serialized.
For example, `data="hello"` produces `data: "hello"` on the wire (with quotes).
###  `` data `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.ServerSentEvent.data "Permanent link")

```
data = None

```

The event payload.
Can be any JSON-serializable value: a Pydantic model, dict, list, string, number, etc. It is **always** serialized to JSON: strings are quoted (`"hello"` becomes `data: "hello"` on the wire).
Mutually exclusive with `raw_data`.
###  `` raw_data `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.ServerSentEvent.raw_data "Permanent link")

```
raw_data = None

```

Raw string to send as the `data:` field **without** JSON encoding.
Use this when you need to send pre-formatted text, HTML fragments, CSV lines, or any non-JSON payload. The string is placed directly into the `data:` field as-is.
Mutually exclusive with `data`.
###  `` event `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.ServerSentEvent.event "Permanent link")

```
event = None

```

Optional event type name.
Maps to `addEventListener(event, ...)` on the browser. When omitted, the browser dispatches on the generic `message` event. Must be a single line.
###  `` id `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.ServerSentEvent.id "Permanent link")

```
id = None

```

Optional event ID.
The browser sends this value back as the `Last-Event-ID` header on automatic reconnection. **Must be a single line** and must not contain null (`\0`) characters.
###  `` retry `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.ServerSentEvent.retry "Permanent link")

```
retry = None

```

Optional reconnection time in **milliseconds**.
Tells the browser how long to wait before reconnecting after the connection is lost. Must be a non-negative integer.
###  `` comment `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/sse/#fastapi.sse.ServerSentEvent.comment "Permanent link")

```
comment = None

```

Optional comment line(s).
Comment lines start with `:` in the SSE wire format and are ignored by `EventSource` clients. Useful for keep-alive pings to prevent proxy/load-balancer timeouts.
