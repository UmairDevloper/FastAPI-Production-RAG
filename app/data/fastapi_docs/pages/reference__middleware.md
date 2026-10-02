# Middleware - FastAPI

Source: https://fastapi.tiangolo.com/reference/middleware/

# Middleware[¶](https://fastapi.tiangolo.com/reference/middleware/#middleware "Permanent link")
There are several middlewares available provided by Starlette directly.
Read more about them in the [FastAPI docs for Middleware](https://fastapi.tiangolo.com/advanced/middleware/).
##  `` fastapi.middleware.cors.CORSMiddleware [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware "Permanent link")

```
CORSMiddleware(
    app,
    allow_origins=(),
    allow_methods=("GET",),
    allow_headers=(),
    allow_credentials=False,
    allow_origin_regex=None,
    allow_private_network=False,
    expose_headers=(),
    max_age=600,
)

```

Source code in `starlette/middleware/cors.py`

```
def __init__(
    self,
    app: ASGIApp,
    allow_origins: Collection[str] = (),
    allow_methods: Collection[str] = ("GET",),
    allow_headers: Collection[str] = (),
    allow_credentials: bool = False,
    allow_origin_regex: str | None = None,
    allow_private_network: bool = False,
    expose_headers: Collection[str] = (),
    max_age: int = 600,
) -> None:
    if "*" in allow_methods:
        allow_methods = ALL_METHODS

    compiled_allow_origin_regex = None
    if allow_origin_regex is not None:
        compiled_allow_origin_regex = re.compile(allow_origin_regex)

    allow_all_origins = "*" in allow_origins
    allow_all_headers = "*" in allow_headers
    preflight_explicit_allow_origin = not allow_all_origins or allow_credentials

    simple_headers: dict[str, str] = {}
    if allow_all_origins:
        simple_headers["Access-Control-Allow-Origin"] = "*"
    if allow_credentials:
        simple_headers["Access-Control-Allow-Credentials"] = "true"
    if expose_headers:
        simple_headers["Access-Control-Expose-Headers"] = ", ".join(expose_headers)

    preflight_headers: dict[str, str] = {
        "Vary": "Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Access-Control-Request-Private-Network"  # noqa: E501  # fmt: skip
    }
    if not preflight_explicit_allow_origin:
        preflight_headers["Access-Control-Allow-Origin"] = "*"
    preflight_headers.update(
        {
            "Access-Control-Allow-Methods": ", ".join(allow_methods),
            "Access-Control-Max-Age": str(max_age),
        }
    )
    allow_headers = sorted(SAFELISTED_HEADERS | set(allow_headers))
    if allow_headers and not allow_all_headers:
        preflight_headers["Access-Control-Allow-Headers"] = ", ".join(allow_headers)
    if allow_credentials:
        preflight_headers["Access-Control-Allow-Credentials"] = "true"

    self.app = app
    self.allow_origins = allow_origins
    self.allow_methods = allow_methods
    self.allow_headers = [h.lower() for h in allow_headers]
    self.allow_all_origins = allow_all_origins
    self.allow_all_headers = allow_all_headers
    self.allow_credentials = allow_credentials
    self.preflight_explicit_allow_origin = preflight_explicit_allow_origin
    self.allow_origin_regex = compiled_allow_origin_regex
    self.allow_private_network = allow_private_network
    self.simple_headers = simple_headers
    self.preflight_headers = preflight_headers

```

###  `` app `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.app "Permanent link")

```
app = app

```

###  `` allow_origins `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_origins "Permanent link")

```
allow_origins = allow_origins

```

###  `` allow_methods `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_methods "Permanent link")

```
allow_methods = allow_methods

```

###  `` allow_headers `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_headers "Permanent link")

```
allow_headers = [(lower()) for h in allow_headers]

```

###  `` allow_all_origins `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_all_origins "Permanent link")

```
allow_all_origins = allow_all_origins

```

###  `` allow_all_headers `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_all_headers "Permanent link")

```
allow_all_headers = allow_all_headers

```

###  `` allow_credentials `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_credentials "Permanent link")

```
allow_credentials = allow_credentials

```

###  `` preflight_explicit_allow_origin `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.preflight_explicit_allow_origin "Permanent link")

```
preflight_explicit_allow_origin = (
    preflight_explicit_allow_origin
)

```

###  `` allow_origin_regex `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_origin_regex "Permanent link")

```
allow_origin_regex = compiled_allow_origin_regex

```

###  `` allow_private_network `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_private_network "Permanent link")

```
allow_private_network = allow_private_network

```

###  `` simple_headers `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.simple_headers "Permanent link")

```
simple_headers = simple_headers

```

###  `` preflight_headers `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.preflight_headers "Permanent link")

```
preflight_headers = preflight_headers

```

###  `` is_allowed_origin [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.is_allowed_origin "Permanent link")

```
is_allowed_origin(origin)

```

Source code in `starlette/middleware/cors.py`

```
def is_allowed_origin(self, origin: str) -> bool:
    if self.allow_all_origins:
        return True

    if self.allow_origin_regex is not None and self.allow_origin_regex.fullmatch(origin):
        return True

    return origin in self.allow_origins

```

###  `` preflight_response [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.preflight_response "Permanent link")

```
preflight_response(request_headers)

```

Source code in `starlette/middleware/cors.py`

```
def preflight_response(self, request_headers: Headers) -> Response:
    requested_origin = request_headers["origin"]
    requested_method = request_headers["access-control-request-method"]
    requested_headers = request_headers.get("access-control-request-headers")
    requested_private_network = request_headers.get("access-control-request-private-network")

    headers = dict(self.preflight_headers)
    failures: list[str] = []

    if self.is_allowed_origin(origin=requested_origin):
        if self.preflight_explicit_allow_origin:
            # The "else" case is already accounted for in self.preflight_headers
            # and the value would be "*".
            headers["Access-Control-Allow-Origin"] = requested_origin
    else:
        failures.append("origin")

    if requested_method not in self.allow_methods:
        failures.append("method")

    # If we allow all headers, then we have to mirror back any requested
    # headers in the response.
    if self.allow_all_headers and requested_headers is not None:
        headers["Access-Control-Allow-Headers"] = requested_headers
    elif requested_headers is not None:
        for header in [h.lower() for h in requested_headers.split(",")]:
            if header.strip() not in self.allow_headers:
                failures.append("headers")
                break

    if requested_private_network is not None:
        if self.allow_private_network:
            headers["Access-Control-Allow-Private-Network"] = "true"
        else:
            failures.append("private-network")

    # We don't strictly need to use 400 responses here, since its up to
    # the browser to enforce the CORS policy, but its more informative
    # if we do.
    if failures:
        failure_text = "Disallowed CORS " + ", ".join(failures)
        return PlainTextResponse(failure_text, status_code=400, headers=headers)

    return PlainTextResponse("OK", status_code=200, headers=headers)

```

###  `` simple_response `async` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.simple_response "Permanent link")

```
simple_response(scope, receive, send, request_headers)

```

Source code in `starlette/middleware/cors.py`

```
async def simple_response(self, scope: Scope, receive: Receive, send: Send, request_headers: Headers) -> None:
    send = functools.partial(self.send, send=send, request_headers=request_headers)
    await self.app(scope, receive, send)

```

###  `` send `async` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.send "Permanent link")

```
send(message, send, request_headers)

```

Source code in `starlette/middleware/cors.py`

```
async def send(self, message: Message, send: Send, request_headers: Headers) -> None:
    if message["type"] != "http.response.start":
        await send(message)
        return

    message.setdefault("headers", [])
    headers = MutableHeaders(scope=message)
    origin = request_headers.get("Origin")
    if origin is not None:
        headers.update(self.simple_headers)

    # If credentials are allowed, then we must respond with the specific origin instead of '*'.
    if origin is not None and self.allow_all_origins and self.allow_credentials:
        self.allow_explicit_origin(headers, origin)

    # If we only allow specific origins, then we have to mirror back the Origin header in the response.
    elif origin is not None and not self.allow_all_origins and self.is_allowed_origin(origin=origin):
        self.allow_explicit_origin(headers, origin)
    else:
        headers["Vary"] = ", ".join([*headers.getlist("Vary"), "Origin"])

    await send(message)

```

###  `` allow_explicit_origin `staticmethod` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.cors.CORSMiddleware.allow_explicit_origin "Permanent link")

```
allow_explicit_origin(headers, origin)

```

Source code in `starlette/middleware/cors.py`

```
@staticmethod
def allow_explicit_origin(headers: MutableHeaders, origin: str) -> None:
    headers["Access-Control-Allow-Origin"] = origin
    headers["Vary"] = ", ".join([*headers.getlist("Vary"), "Origin"])

```

It can be imported from `fastapi`:

```
from fastapi.middleware.cors import CORSMiddleware

```

##  `` fastapi.middleware.gzip.GZipMiddleware [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.gzip.GZipMiddleware "Permanent link")

```
GZipMiddleware(
    app,
    minimum_size=500,
    compresslevel=9,
    thread_minimum_size=128 * 1024,
    *,
    exclude_content_types=DEFAULT_EXCLUDED_CONTENT_TYPES
)

```

Source code in `starlette/middleware/gzip.py`

```
def __init__(
    self,
    app: ASGIApp,
    minimum_size: int = 500,
    compresslevel: int = 9,
    thread_minimum_size: int = 128 * 1024,  # 128 KiB
    *,
    exclude_content_types: tuple[str, ...] = DEFAULT_EXCLUDED_CONTENT_TYPES,
) -> None:
    self.app = app
    self.minimum_size = minimum_size
    self.compresslevel = compresslevel
    self.thread_minimum_size = thread_minimum_size
    self.exclude_content_types = _normalize_content_types(exclude_content_types)

```

###  `` app `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.gzip.GZipMiddleware.app "Permanent link")

```
app = app

```

###  `` minimum_size `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.gzip.GZipMiddleware.minimum_size "Permanent link")

```
minimum_size = minimum_size

```

###  `` compresslevel `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.gzip.GZipMiddleware.compresslevel "Permanent link")

```
compresslevel = compresslevel

```

###  `` thread_minimum_size `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.gzip.GZipMiddleware.thread_minimum_size "Permanent link")

```
thread_minimum_size = thread_minimum_size

```

###  `` exclude_content_types `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.gzip.GZipMiddleware.exclude_content_types "Permanent link")

```
exclude_content_types = _normalize_content_types(
    exclude_content_types
)

```

It can be imported from `fastapi`:

```
from fastapi.middleware.gzip import GZipMiddleware

```

##  `` fastapi.middleware.httpsredirect.HTTPSRedirectMiddleware [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.httpsredirect.HTTPSRedirectMiddleware "Permanent link")

```
HTTPSRedirectMiddleware(app)

```

Source code in `starlette/middleware/httpsredirect.py`

```
def __init__(self, app: ASGIApp) -> None:
    self.app = app

```

###  `` app `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.httpsredirect.HTTPSRedirectMiddleware.app "Permanent link")

```
app = app

```

It can be imported from `fastapi`:

```
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

```

##  `` fastapi.middleware.trustedhost.TrustedHostMiddleware [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.trustedhost.TrustedHostMiddleware "Permanent link")

```
TrustedHostMiddleware(
    app, allowed_hosts=None, www_redirect=True
)

```

Source code in `starlette/middleware/trustedhost.py`

```
def __init__(
    self,
    app: ASGIApp,
    allowed_hosts: Sequence[str] | None = None,
    www_redirect: bool = True,
) -> None:
    if allowed_hosts is None:
        allowed_hosts = ["*"]

    for pattern in allowed_hosts:
        assert "*" not in pattern[1:], ENFORCE_DOMAIN_WILDCARD
        if pattern.startswith("*") and pattern != "*":
            assert pattern.startswith("*."), ENFORCE_DOMAIN_WILDCARD
    self.app = app
    self.allowed_hosts = list(allowed_hosts)
    self.allow_any = "*" in allowed_hosts
    self.www_redirect = www_redirect

```

###  `` app `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.trustedhost.TrustedHostMiddleware.app "Permanent link")

```
app = app

```

###  `` allowed_hosts `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.trustedhost.TrustedHostMiddleware.allowed_hosts "Permanent link")

```
allowed_hosts = list[](https://fastapi.tiangolo.com/python-types/#list "List \(<code>list</code>\)")(allowed_hosts)

```

###  `` allow_any `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.trustedhost.TrustedHostMiddleware.allow_any "Permanent link")

```
allow_any = '*' in allowed_hosts

```

###  `` www_redirect `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/middleware/#fastapi.middleware.trustedhost.TrustedHostMiddleware.www_redirect "Permanent link")

```
www_redirect = www_redirect

```

It can be imported from `fastapi`:

```
from fastapi.middleware.trustedhost import TrustedHostMiddleware

```

