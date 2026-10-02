# HTTPConnection class - FastAPI

Source: https://fastapi.tiangolo.com/reference/httpconnection/

#  `HTTPConnection` class[¶](https://fastapi.tiangolo.com/reference/httpconnection/#httpconnection-class "Permanent link")
When you want to define dependencies that should be compatible with both HTTP and WebSockets, you can define a parameter that takes an `HTTPConnection` instead of a `Request` or a `WebSocket`.
You can import it from `fastapi.requests`:

```
from fastapi.requests import HTTPConnection

```

##  `` fastapi.requests.HTTPConnection [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection "Permanent link")

```
HTTPConnection(scope, receive=None)

```

Bases: `Mapping[str, Any]`, `Generic[StateT]`
A base class for incoming HTTP connections, that is used to provide any functionality that is common to both `Request` and `WebSocket`.
Source code in `starlette/requests.py`

```
def __init__(self, scope: Scope, receive: Receive | None = None) -> None:
    assert scope["type"] in ("http", "websocket")
    self.scope = scope

```

###  `` scope `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.scope "Permanent link")

```
scope = scope

```

###  `` app `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.app "Permanent link")

```
app

```

###  `` url `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.url "Permanent link")

```
url

```

###  `` base_url `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.base_url "Permanent link")

```
base_url

```

###  `` headers `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.headers "Permanent link")

```
headers

```

###  `` query_params `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.query_params "Permanent link")

```
query_params

```

###  `` path_params `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.path_params "Permanent link")

```
path_params

```

###  `` cookies `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.cookies "Permanent link")

```
cookies

```

###  `` client `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.client "Permanent link")

```
client

```

###  `` session `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.session "Permanent link")

```
session

```

###  `` auth `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.auth "Permanent link")

```
auth

```

###  `` user `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.user "Permanent link")

```
user

```

###  `` state `property` [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.state "Permanent link")

```
state

```

###  `` url_for [¶](https://fastapi.tiangolo.com/reference/httpconnection/#fastapi.requests.HTTPConnection.url_for "Permanent link")

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

