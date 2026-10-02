# Custom Response Classes - File, HTML, Redirect, Streaming, etc. - FastAPI

Source: https://fastapi.tiangolo.com/reference/responses/

# Custom Response Classes - File, HTML, Redirect, Streaming, etc.[¶](https://fastapi.tiangolo.com/reference/responses/#custom-response-classes-file-html-redirect-streaming-etc "Permanent link")
There are several custom response classes you can use to create an instance and return them directly from your _path operations_.
Read more about it in the [FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/).
You can import them directly from `fastapi.responses`:

```
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    ORJSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
    UJSONResponse,
)

```

## FastAPI Responses[¶](https://fastapi.tiangolo.com/reference/responses/#fastapi-responses "Permanent link")
There were a couple of custom FastAPI response classes that were intended to optimize JSON performance.
However, they are now deprecated as you will now get better performance by using a [Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/).
That way, Pydantic will serialize the data into JSON bytes on the Rust side, which will achieve better performance than these custom JSON responses.
Read more about it in [Custom Response - HTML, Stream, File, others - `orjson` or Response Model](https://fastapi.tiangolo.com/advanced/custom-response/#orjson-or-response-model).
##  `` fastapi.responses.UJSONResponse [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse "Permanent link")

```
UJSONResponse(
    content,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Bases: `JSONResponse[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.JSONResponse</span> \(<code>starlette.responses.JSONResponse</code>\)")`
JSON response using the ujson library to serialize data to JSON.
**Deprecated** : `UJSONResponse` is deprecated. FastAPI now serializes data directly to JSON bytes via Pydantic when a return type or response model is set, which is faster and doesn't need a custom response class.
Read more in the [FastAPI docs for Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/#orjson-or-response-model) and the [FastAPI docs for Response Model](https://fastapi.tiangolo.com/tutorial/response-model/).
**Note** : `ujson` is not included with FastAPI and must be installed separately, e.g. `pip install ujson`.
Source code in `starlette/responses.py`

```
def __init__(
    self,
    content: Any,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> None:
    super().__init__(content, status_code, headers, media_type, background)

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.media_type "Permanent link")

```
media_type = 'application/json'

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.render "Permanent link")

```
render(content)

```

Source code in `fastapi/responses.py`

```
def render(self, content: Any) -> bytes:
    assert ujson is not None, "ujson must be installed to use UJSONResponse"
    return ujson.dumps(content, ensure_ascii=False).encode("utf-8")

```

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.UJSONResponse.delete_cookie "Permanent link")

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

##  `` fastapi.responses.ORJSONResponse [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse "Permanent link")

```
ORJSONResponse(
    content,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Bases: `JSONResponse[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.JSONResponse</span> \(<code>starlette.responses.JSONResponse</code>\)")`
JSON response using the orjson library to serialize data to JSON.
**Deprecated** : `ORJSONResponse` is deprecated. FastAPI now serializes data directly to JSON bytes via Pydantic when a return type or response model is set, which is faster and doesn't need a custom response class.
Read more in the [FastAPI docs for Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/#orjson-or-response-model) and the [FastAPI docs for Response Model](https://fastapi.tiangolo.com/tutorial/response-model/).
**Note** : `orjson` is not included with FastAPI and must be installed separately, e.g. `pip install orjson`.
Source code in `starlette/responses.py`

```
def __init__(
    self,
    content: Any,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> None:
    super().__init__(content, status_code, headers, media_type, background)

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.media_type "Permanent link")

```
media_type = 'application/json'

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.render "Permanent link")

```
render(content)

```

Source code in `fastapi/responses.py`

```
def render(self, content: Any) -> bytes:
    assert orjson is not None, "orjson must be installed to use ORJSONResponse"
    return orjson.dumps(
        content, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
    )

```

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.ORJSONResponse.delete_cookie "Permanent link")

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

## Starlette Responses[¶](https://fastapi.tiangolo.com/reference/responses/#starlette-responses "Permanent link")
You can read more about all of them in the [FastAPI docs for Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/) and in the [Starlette docs about Responses](https://starlette.dev/responses/).
##  `` fastapi.responses.FileResponse [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse "Permanent link")

```
FileResponse(
    path,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
    filename=None,
    stat_result=None,
    content_disposition_type="attachment",
)

```

Bases: `Response[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.Response</span> \(<code>starlette.responses.Response</code>\)")`
Source code in `starlette/responses.py`

```
def __init__(
    self,
    path: str | os.PathLike[str],
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
    filename: str | None = None,
    stat_result: os.stat_result | None = None,
    content_disposition_type: str = "attachment",
) -> None:
    self.path = path
    self.status_code = status_code
    self.filename = filename
    if media_type is None:
        media_type = guess_type(filename or path)[0] or "application/octet-stream"
    self.media_type = media_type
    self.background = background
    self.init_headers(headers)
    self.headers.setdefault("accept-ranges", "bytes")
    if self.filename is not None:
        content_disposition_filename = quote(self.filename)
        if content_disposition_filename != self.filename:
            content_disposition = f"{content_disposition_type}; filename*=utf-8''{content_disposition_filename}"
        else:
            content_disposition = f'{content_disposition_type}; filename="{self.filename}"'
        self.headers.setdefault("content-disposition", content_disposition)
    self.stat_result = stat_result
    if stat_result is not None:
        self.set_stat_headers(stat_result)

```

###  `` chunk_size `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.chunk_size "Permanent link")

```
chunk_size = 64 * 1024

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.media_type "Permanent link")

```
media_type = media_type

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.render "Permanent link")

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

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.FileResponse.delete_cookie "Permanent link")

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

##  `` fastapi.responses.HTMLResponse [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse "Permanent link")

```
HTMLResponse(
    content=None,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Bases: `Response[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.Response</span> \(<code>starlette.responses.Response</code>\)")`
Source code in `starlette/responses.py`

```
def __init__(
    self,
    content: Any = None,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> None:
    self.status_code = status_code
    if media_type is not None:
        self.media_type = media_type
    self.background = background
    self.body = self.render(content)
    self.init_headers(headers)

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.media_type "Permanent link")

```
media_type = 'text/html'

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.render "Permanent link")

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

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.HTMLResponse.delete_cookie "Permanent link")

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

##  `` fastapi.responses.JSONResponse [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse "Permanent link")

```
JSONResponse(
    content,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Bases: `Response[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.Response</span> \(<code>starlette.responses.Response</code>\)")`
Source code in `starlette/responses.py`

```
def __init__(
    self,
    content: Any,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> None:
    super().__init__(content, status_code, headers, media_type, background)

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.media_type "Permanent link")

```
media_type = 'application/json'

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.render "Permanent link")

```
render(content)

```

Source code in `starlette/responses.py`

```
def render(self, content: Any) -> bytes:
    return json.dumps(
        content,
        ensure_ascii=False,
        allow_nan=False,
        indent=None,
        separators=(",", ":"),
    ).encode("utf-8")

```

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.JSONResponse.delete_cookie "Permanent link")

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

##  `` fastapi.responses.PlainTextResponse [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse "Permanent link")

```
PlainTextResponse(
    content=None,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Bases: `Response[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.Response</span> \(<code>starlette.responses.Response</code>\)")`
Source code in `starlette/responses.py`

```
def __init__(
    self,
    content: Any = None,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> None:
    self.status_code = status_code
    if media_type is not None:
        self.media_type = media_type
    self.background = background
    self.body = self.render(content)
    self.init_headers(headers)

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.media_type "Permanent link")

```
media_type = 'text/plain'

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.render "Permanent link")

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

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.PlainTextResponse.delete_cookie "Permanent link")

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

##  `` fastapi.responses.RedirectResponse [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse "Permanent link")

```
RedirectResponse(
    url, status_code=307, headers=None, background=None
)

```

Bases: `Response[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.Response</span> \(<code>starlette.responses.Response</code>\)")`
Source code in `starlette/responses.py`

```
def __init__(
    self,
    url: str | URL,
    status_code: int = 307,
    headers: Mapping[str, str] | None = None,
    background: BackgroundTask | None = None,
) -> None:
    super().__init__(content=b"", status_code=status_code, headers=headers, background=background)
    self.headers["location"] = quote(str(url), safe=":/%#?=@[]!$&'()*+,;")

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.media_type "Permanent link")

```
media_type = None

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.render "Permanent link")

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

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.RedirectResponse.delete_cookie "Permanent link")

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

##  `` fastapi.responses.Response [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response "Permanent link")

```
Response(
    content=None,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Source code in `starlette/responses.py`

```
def __init__(
    self,
    content: Any = None,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> None:
    self.status_code = status_code
    if media_type is not None:
        self.media_type = media_type
    self.background = background
    self.body = self.render(content)
    self.init_headers(headers)

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.media_type "Permanent link")

```
media_type = None

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.render "Permanent link")

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

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response.delete_cookie "Permanent link")

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

##  `` fastapi.responses.StreamingResponse [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse "Permanent link")

```
StreamingResponse(
    content,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Bases: `Response[](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.Response "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.responses.Response</span> \(<code>starlette.responses.Response</code>\)")`
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

###  `` body_iterator `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.body_iterator "Permanent link")

```
body_iterator

```

###  `` charset `class-attribute` `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.charset "Permanent link")

```
charset = 'utf-8'

```

###  `` status_code `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.status_code "Permanent link")

```
status_code = status_code

```

###  `` media_type `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.media_type "Permanent link")

```
media_type = (
    media_type if media_type is None else media_type
)

```

###  `` body `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.body "Permanent link")

```
body = render(content)

```

###  `` background `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.background "Permanent link")

```
background = background

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.headers "Permanent link")

```
headers

```

###  `` render [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.render "Permanent link")

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

###  `` init_headers [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.init_headers "Permanent link")

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

###  `` set_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.set_cookie "Permanent link")

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

###  `` delete_cookie [¶](https://fastapi.tiangolo.com/reference/responses/#fastapi.responses.StreamingResponse.delete_cookie "Permanent link")

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

