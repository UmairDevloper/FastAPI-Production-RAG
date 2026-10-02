# Security Tools - FastAPI

Source: https://fastapi.tiangolo.com/reference/security/

# Security Tools[¶](https://fastapi.tiangolo.com/reference/security/#security-tools "Permanent link")
When you need to declare dependencies with OAuth2 scopes you use `Security()`.
But you still need to define what is the dependable, the callable that you pass as a parameter to `Depends()` or `Security()`.
There are multiple tools that you can use to create those dependables, and they get integrated into OpenAPI so they are shown in the automatic docs UI, they can be used by automatically generated clients and SDKs, etc.
You can import them from `fastapi.security`:

```
from fastapi.security import (
    APIKeyCookie,
    APIKeyHeader,
    APIKeyQuery,
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
    HTTPDigest,
    OAuth2,
    OAuth2AuthorizationCodeBearer,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    OAuth2PasswordRequestFormStrict,
    OpenIdConnect,
    SecurityScopes,
)

```

Read more about them in the [FastAPI docs about Security](https://fastapi.tiangolo.com/tutorial/security/).
## API Key Security Schemes[¶](https://fastapi.tiangolo.com/reference/security/#api-key-security-schemes "Permanent link")
##  `` fastapi.security.APIKeyCookie [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyCookie "Permanent link")

```
APIKeyCookie(
    *,
    name,
    scheme_name=None,
    description=None,
    auto_error=True
)

```

Bases: `APIKeyBase`
API key authentication using a cookie.
This defines the name of the cookie that should be provided in the request with the API key and integrates that into the OpenAPI documentation. It extracts the key value sent in the cookie automatically and provides it as the dependency result. But it doesn't define how to set that cookie.
#### Usage[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyCookie--usage "Permanent link")
Create an instance object and use that object as the dependency in `Depends()`.
The dependency result will be a string containing the key value.
#### Example[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyCookie--example "Permanent link")

```
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyCookie

app = FastAPI()

cookie_scheme = APIKeyCookie(name="session")


@app.get("/items/")
async def read_items(session: str = Depends(cookie_scheme)):
    return {"session": session}

```
  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `name`  |  Cookie name. **TYPE:** `str`  |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if the cookie is not provided, `APIKeyCookie` will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the cookie is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, in a cookie or in an HTTP Bearer token). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/api_key.py`

```
def __init__(
    self,
    *,
    name: Annotated[str, Doc("Cookie name.")],
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if the cookie is not provided, `APIKeyCookie` will
            automatically cancel the request and send the client an error.

            If `auto_error` is set to `False`, when the cookie is not available,
            instead of erroring out, the dependency result will be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, in a cookie or
            in an HTTP Bearer token).
            """
        ),
    ] = True,
):
    super().__init__(
        location=APIKeyIn.cookie,
        name=name,
        scheme_name=scheme_name,
        description=description,
        auto_error=auto_error,
    )

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyCookie.model "Permanent link")

```
model = APIKey[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.APIKey "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">APIKey</span> \(<code>fastapi.openapi.models.APIKey</code>\)")(
    **{"in": location}, name=name, description=description
)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyCookie.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyCookie.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyCookie.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

The WWW-Authenticate header is not standardized for API Key authentication but the HTTP specification requires that an error of 401 "Unauthorized" must include a WWW-Authenticate header.
Ref: https://datatracker.ietf.org/doc/html/rfc9110#name-401-unauthorized
For this, this method sends a custom challenge `APIKey`.
Source code in `fastapi/security/api_key.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    """
    The WWW-Authenticate header is not standardized for API Key authentication but
    the HTTP specification requires that an error of 401 "Unauthorized" must
    include a WWW-Authenticate header.

    Ref: https://datatracker.ietf.org/doc/html/rfc9110#name-401-unauthorized

    For this, this method sends a custom challenge `APIKey`.
    """
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "APIKey"},
    )

```

###  `` check_api_key [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyCookie.check_api_key "Permanent link")

```
check_api_key(api_key)

```

Source code in `fastapi/security/api_key.py`

```
def check_api_key(self, api_key: str | None) -> str | None:
    if not api_key:
        if self.auto_error:
            raise self.make_not_authenticated_error()
        return None
    return api_key

```

##  `` fastapi.security.APIKeyHeader [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader "Permanent link")

```
APIKeyHeader(
    *,
    name,
    scheme_name=None,
    description=None,
    auto_error=True
)

```

Bases: `APIKeyBase`
API key authentication using a header.
This defines the name of the header that should be provided in the request with the API key and integrates that into the OpenAPI documentation. It extracts the key value sent in the header automatically and provides it as the dependency result. But it doesn't define how to send that key to the client.
#### Usage[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader--usage "Permanent link")
Create an instance object and use that object as the dependency in `Depends()`.
The dependency result will be a string containing the key value.
#### Example[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader--example "Permanent link")

```
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader

app = FastAPI()

header_scheme = APIKeyHeader(name="x-key")


@app.get("/items/")
async def read_items(key: str = Depends(header_scheme)):
    return {"key": key}

```
  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `name`  |  Header name. **TYPE:** `str`  |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if the header is not provided, `APIKeyHeader` will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the header is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, in a header or in an HTTP Bearer token). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/api_key.py`

```
def __init__(
    self,
    *,
    name: Annotated[str, Doc("Header name.")],
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if the header is not provided, `APIKeyHeader` will
            automatically cancel the request and send the client an error.

            If `auto_error` is set to `False`, when the header is not available,
            instead of erroring out, the dependency result will be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, in a header or
            in an HTTP Bearer token).
            """
        ),
    ] = True,
):
    super().__init__(
        location=APIKeyIn.header,
        name=name,
        scheme_name=scheme_name,
        description=description,
        auto_error=auto_error,
    )

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader.model "Permanent link")

```
model = APIKey[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.APIKey "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">APIKey</span> \(<code>fastapi.openapi.models.APIKey</code>\)")(
    **{"in": location}, name=name, description=description
)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

The WWW-Authenticate header is not standardized for API Key authentication but the HTTP specification requires that an error of 401 "Unauthorized" must include a WWW-Authenticate header.
Ref: https://datatracker.ietf.org/doc/html/rfc9110#name-401-unauthorized
For this, this method sends a custom challenge `APIKey`.
Source code in `fastapi/security/api_key.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    """
    The WWW-Authenticate header is not standardized for API Key authentication but
    the HTTP specification requires that an error of 401 "Unauthorized" must
    include a WWW-Authenticate header.

    Ref: https://datatracker.ietf.org/doc/html/rfc9110#name-401-unauthorized

    For this, this method sends a custom challenge `APIKey`.
    """
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "APIKey"},
    )

```

###  `` check_api_key [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyHeader.check_api_key "Permanent link")

```
check_api_key(api_key)

```

Source code in `fastapi/security/api_key.py`

```
def check_api_key(self, api_key: str | None) -> str | None:
    if not api_key:
        if self.auto_error:
            raise self.make_not_authenticated_error()
        return None
    return api_key

```

##  `` fastapi.security.APIKeyQuery [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyQuery "Permanent link")

```
APIKeyQuery(
    *,
    name,
    scheme_name=None,
    description=None,
    auto_error=True
)

```

Bases: `APIKeyBase`
API key authentication using a query parameter.
This defines the name of the query parameter that should be provided in the request with the API key and integrates that into the OpenAPI documentation. It extracts the key value sent in the query parameter automatically and provides it as the dependency result. But it doesn't define how to send that API key to the client.
#### Usage[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyQuery--usage "Permanent link")
Create an instance object and use that object as the dependency in `Depends()`.
The dependency result will be a string containing the key value.
#### Example[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyQuery--example "Permanent link")

```
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyQuery

app = FastAPI()

query_scheme = APIKeyQuery(name="api_key")


@app.get("/items/")
async def read_items(api_key: str = Depends(query_scheme)):
    return {"api_key": api_key}

```
  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `name`  |  Query parameter name. **TYPE:** `str`  |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if the query parameter is not provided, `APIKeyQuery` will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the query parameter is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, in a query parameter or in an HTTP Bearer token). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/api_key.py`

```
def __init__(
    self,
    *,
    name: Annotated[
        str,
        Doc("Query parameter name."),
    ],
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if the query parameter is not provided, `APIKeyQuery` will
            automatically cancel the request and send the client an error.

            If `auto_error` is set to `False`, when the query parameter is not
            available, instead of erroring out, the dependency result will be
            `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, in a query
            parameter or in an HTTP Bearer token).
            """
        ),
    ] = True,
):
    super().__init__(
        location=APIKeyIn.query,
        name=name,
        scheme_name=scheme_name,
        description=description,
        auto_error=auto_error,
    )

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyQuery.model "Permanent link")

```
model = APIKey[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.APIKey "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">APIKey</span> \(<code>fastapi.openapi.models.APIKey</code>\)")(
    **{"in": location}, name=name, description=description
)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyQuery.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyQuery.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyQuery.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

The WWW-Authenticate header is not standardized for API Key authentication but the HTTP specification requires that an error of 401 "Unauthorized" must include a WWW-Authenticate header.
Ref: https://datatracker.ietf.org/doc/html/rfc9110#name-401-unauthorized
For this, this method sends a custom challenge `APIKey`.
Source code in `fastapi/security/api_key.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    """
    The WWW-Authenticate header is not standardized for API Key authentication but
    the HTTP specification requires that an error of 401 "Unauthorized" must
    include a WWW-Authenticate header.

    Ref: https://datatracker.ietf.org/doc/html/rfc9110#name-401-unauthorized

    For this, this method sends a custom challenge `APIKey`.
    """
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "APIKey"},
    )

```

###  `` check_api_key [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.APIKeyQuery.check_api_key "Permanent link")

```
check_api_key(api_key)

```

Source code in `fastapi/security/api_key.py`

```
def check_api_key(self, api_key: str | None) -> str | None:
    if not api_key:
        if self.auto_error:
            raise self.make_not_authenticated_error()
        return None
    return api_key

```

## HTTP Authentication Schemes[¶](https://fastapi.tiangolo.com/reference/security/#http-authentication-schemes "Permanent link")
##  `` fastapi.security.HTTPBasic [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic "Permanent link")

```
HTTPBasic(
    *,
    scheme_name=None,
    realm=None,
    description=None,
    auto_error=True
)

```

Bases: `HTTPBase`
HTTP Basic authentication.
Ref: https://datatracker.ietf.org/doc/html/rfc7617
#### Usage[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic--usage "Permanent link")
Create an instance object and use that object as the dependency in `Depends()`.
The dependency result will be an `HTTPBasicCredentials` object containing the `username` and the `password`.
Read more about it in the [FastAPI docs for HTTP Basic Auth](https://fastapi.tiangolo.com/advanced/security/http-basic-auth/).
#### Example[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic--example "Permanent link")

```
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()

security = HTTPBasic()


@app.get("/users/me")
def read_current_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    return {"username": credentials.username, "password": credentials.password}

```
  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `realm`  |  HTTP Basic authentication realm. **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if the HTTP Basic authentication is not provided (a header), `HTTPBasic` will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the HTTP Basic authentication is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, in HTTP Basic authentication or in an HTTP Bearer token). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/http.py`

```
def __init__(
    self,
    *,
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    realm: Annotated[
        str | None,
        Doc(
            """
            HTTP Basic authentication realm.
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if the HTTP Basic authentication is not provided (a
            header), `HTTPBasic` will automatically cancel the request and send the
            client an error.

            If `auto_error` is set to `False`, when the HTTP Basic authentication
            is not available, instead of erroring out, the dependency result will
            be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, in HTTP Basic
            authentication or in an HTTP Bearer token).
            """
        ),
    ] = True,
):
    self.model = HTTPBaseModel(scheme="basic", description=description)
    self.scheme_name = scheme_name or self.__class__.__name__
    self.realm = realm
    self.auto_error = auto_error

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic.model "Permanent link")

```
model = HTTPBase[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.HTTPBase "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">HTTPBase</span> \(<code>fastapi.openapi.models.HTTPBase</code>\)")(scheme='basic', description=description)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` realm `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic.realm "Permanent link")

```
realm = realm

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

Source code in `fastapi/security/http.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers=self.make_authenticate_headers(),
    )

```

###  `` make_authenticate_headers [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasic.make_authenticate_headers "Permanent link")

```
make_authenticate_headers()

```

Source code in `fastapi/security/http.py`

```
def make_authenticate_headers(self) -> dict[str, str]:
    if self.realm:
        return {"WWW-Authenticate": f'Basic realm="{self.realm}"'}
    return {"WWW-Authenticate": "Basic"}

```

##  `` fastapi.security.HTTPBearer [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer "Permanent link")

```
HTTPBearer(
    *,
    bearerFormat=None,
    scheme_name=None,
    description=None,
    auto_error=True
)

```

Bases: `HTTPBase`
HTTP Bearer token authentication.
#### Usage[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer--usage "Permanent link")
Create an instance object and use that object as the dependency in `Depends()`.
The dependency result will be an `HTTPAuthorizationCredentials` object containing the `scheme` and the `credentials`.
#### Example[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer--example "Permanent link")

```
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

app = FastAPI()

security = HTTPBearer()


@app.get("/users/me")
def read_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
):
    return {"scheme": credentials.scheme, "credentials": credentials.credentials}

```
  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `bearerFormat`  |  Bearer token format. **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if the HTTP Bearer token is not provided (in an `Authorization` header), `HTTPBearer` will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the HTTP Bearer token is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, in an HTTP Bearer token or in a cookie). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/http.py`

```
def __init__(
    self,
    *,
    bearerFormat: Annotated[str | None, Doc("Bearer token format.")] = None,
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if the HTTP Bearer token is not provided (in an
            `Authorization` header), `HTTPBearer` will automatically cancel the
            request and send the client an error.

            If `auto_error` is set to `False`, when the HTTP Bearer token
            is not available, instead of erroring out, the dependency result will
            be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, in an HTTP
            Bearer token or in a cookie).
            """
        ),
    ] = True,
):
    self.model = HTTPBearerModel(bearerFormat=bearerFormat, description=description)
    self.scheme_name = scheme_name or self.__class__.__name__
    self.auto_error = auto_error

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer.model "Permanent link")

```
model = HTTPBearer[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.HTTPBearer "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">HTTPBearer</span> \(<code>fastapi.openapi.models.HTTPBearer</code>\)")(
    bearerFormat=bearerFormat, description=description
)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_authenticate_headers [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer.make_authenticate_headers "Permanent link")

```
make_authenticate_headers()

```

Source code in `fastapi/security/http.py`

```
def make_authenticate_headers(self) -> dict[str, str]:
    return {"WWW-Authenticate": f"{self.model.scheme.title()}"}

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

Source code in `fastapi/security/http.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers=self.make_authenticate_headers(),
    )

```

##  `` fastapi.security.HTTPDigest [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest "Permanent link")

```
HTTPDigest(
    *, scheme_name=None, description=None, auto_error=True
)

```

Bases: `HTTPBase`
HTTP Digest authentication.
**Warning** : this is only a stub to connect the components with OpenAPI in FastAPI, but it doesn't implement the full Digest scheme, you would need to subclass it and implement it in your code.
Ref: https://datatracker.ietf.org/doc/html/rfc7616
#### Usage[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest--usage "Permanent link")
Create an instance object and use that object as the dependency in `Depends()`.
The dependency result will be an `HTTPAuthorizationCredentials` object containing the `scheme` and the `credentials`.
#### Example[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest--example "Permanent link")

```
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPDigest

app = FastAPI()

security = HTTPDigest()


@app.get("/users/me")
def read_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
):
    return {"scheme": credentials.scheme, "credentials": credentials.credentials}

```
  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if the HTTP Digest is not provided, `HTTPDigest` will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the HTTP Digest is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, in HTTP Digest or in a cookie). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/http.py`

```
def __init__(
    self,
    *,
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if the HTTP Digest is not provided, `HTTPDigest` will
            automatically cancel the request and send the client an error.

            If `auto_error` is set to `False`, when the HTTP Digest is not
            available, instead of erroring out, the dependency result will
            be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, in HTTP
            Digest or in a cookie).
            """
        ),
    ] = True,
):
    self.model = HTTPBaseModel(scheme="digest", description=description)
    self.scheme_name = scheme_name or self.__class__.__name__
    self.auto_error = auto_error

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest.model "Permanent link")

```
model = HTTPBase[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.HTTPBase "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">HTTPBase</span> \(<code>fastapi.openapi.models.HTTPBase</code>\)")(scheme='digest', description=description)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_authenticate_headers [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest.make_authenticate_headers "Permanent link")

```
make_authenticate_headers()

```

Source code in `fastapi/security/http.py`

```
def make_authenticate_headers(self) -> dict[str, str]:
    return {"WWW-Authenticate": f"{self.model.scheme.title()}"}

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

Source code in `fastapi/security/http.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers=self.make_authenticate_headers(),
    )

```

## HTTP Credentials[¶](https://fastapi.tiangolo.com/reference/security/#http-credentials "Permanent link")
##  `` fastapi.security.HTTPAuthorizationCredentials [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPAuthorizationCredentials "Permanent link")
Bases: `BaseModel`
The HTTP authorization credentials in the result of using `HTTPBearer` or `HTTPDigest` in a dependency.
The HTTP authorization header value is split by the first space.
The first part is the `scheme`, the second part is the `credentials`.
For example, in an HTTP Bearer token scheme, the client will send a header like:

```
Authorization: Bearer deadbeef12346

```

In this case:
  * `scheme` will have the value `"Bearer"`
  * `credentials` will have the value `"deadbeef12346"`


###  `` scheme `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPAuthorizationCredentials.scheme "Permanent link")

```
scheme

```

The HTTP authorization scheme extracted from the header value.
###  `` credentials `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPAuthorizationCredentials.credentials "Permanent link")

```
credentials

```

The HTTP authorization credentials extracted from the header value.
##  `` fastapi.security.HTTPBasicCredentials [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasicCredentials "Permanent link")
Bases: `BaseModel`
The HTTP Basic credentials given as the result of using `HTTPBasic` in a dependency.
Read more about it in the [FastAPI docs for HTTP Basic Auth](https://fastapi.tiangolo.com/advanced/security/http-basic-auth/).
###  `` username `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasicCredentials.username "Permanent link")

```
username

```

The HTTP Basic username.
###  `` password `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBasicCredentials.password "Permanent link")

```
password

```

The HTTP Basic password.
## OAuth2 Authentication[¶](https://fastapi.tiangolo.com/reference/security/#oauth2-authentication "Permanent link")
##  `` fastapi.security.OAuth2 [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2 "Permanent link")

```
OAuth2(
    *,
    flows=OAuthFlows[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuthFlows "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuthFlows</span> \(<code>fastapi.openapi.models.OAuthFlows</code>\)")(),
    scheme_name=None,
    description=None,
    auto_error=True
)

```

Bases: `SecurityBase`
This is the base class for OAuth2 authentication, an instance of it would be used as a dependency. All other OAuth2 classes inherit from it and customize it for each OAuth2 flow.
You normally would not create a new class inheriting from it but use one of the existing subclasses, and maybe compose them if you want to support multiple flows.
Read more about it in the [FastAPI docs for Security](https://fastapi.tiangolo.com/tutorial/security/).  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `flows`  |  The dictionary of OAuth2 flows. **TYPE:** `OAuthFlows[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuthFlows "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuthFlows</span> \(<code>fastapi.openapi.models.OAuthFlows</code>\)") | dict[](https://fastapi.tiangolo.com/python-types/#dict "Dict \(<code>dict</code>\)")[str, dict[](https://fastapi.tiangolo.com/python-types/#dict "Dict \(<code>dict</code>\)")[str, Any]]` **DEFAULT:** `OAuthFlows[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuthFlows "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuthFlows</span> \(<code>fastapi.openapi.models.OAuthFlows</code>\)")()`  |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if no HTTP Authorization header is provided, required for OAuth2 authentication, it will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the HTTP Authorization header is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, with OAuth2 or in a cookie). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/oauth2.py`

```
def __init__(
    self,
    *,
    flows: Annotated[
        OAuthFlowsModel | dict[str, dict[str, Any]],
        Doc(
            """
            The dictionary of OAuth2 flows.
            """
        ),
    ] = OAuthFlowsModel(),
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if no HTTP Authorization header is provided, required for
            OAuth2 authentication, it will automatically cancel the request and
            send the client an error.

            If `auto_error` is set to `False`, when the HTTP Authorization header
            is not available, instead of erroring out, the dependency result will
            be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, with OAuth2
            or in a cookie).
            """
        ),
    ] = True,
):
    self.model = OAuth2Model(
        flows=cast(OAuthFlowsModel, flows), description=description
    )
    self.scheme_name = scheme_name or self.__class__.__name__
    self.auto_error = auto_error

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2.model "Permanent link")

```
model = OAuth2[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuth2 "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuth2</span> \(<code>fastapi.openapi.models.OAuth2</code>\)")(
    flows=cast(OAuthFlows[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuthFlows "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuthFlows</span> \(<code>fastapi.openapi.models.OAuthFlows</code>\)"), flows), description=description
)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

The OAuth 2 specification doesn't define the challenge that should be used, because a `Bearer` token is not really the only option to authenticate.
But declaring any other authentication challenge would be application-specific as it's not defined in the specification.
For practical reasons, this method uses the `Bearer` challenge by default, as it's probably the most common one.
If you are implementing an OAuth2 authentication scheme other than the provided ones in FastAPI (based on bearer tokens), you might want to override this.
Ref: https://datatracker.ietf.org/doc/html/rfc6749
Source code in `fastapi/security/oauth2.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    """
    The OAuth 2 specification doesn't define the challenge that should be used,
    because a `Bearer` token is not really the only option to authenticate.

    But declaring any other authentication challenge would be application-specific
    as it's not defined in the specification.

    For practical reasons, this method uses the `Bearer` challenge by default, as
    it's probably the most common one.

    If you are implementing an OAuth2 authentication scheme other than the provided
    ones in FastAPI (based on bearer tokens), you might want to override this.

    Ref: https://datatracker.ietf.org/doc/html/rfc6749
    """
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

```

##  `` fastapi.security.OAuth2AuthorizationCodeBearer [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2AuthorizationCodeBearer "Permanent link")

```
OAuth2AuthorizationCodeBearer(
    authorizationUrl,
    tokenUrl,
    refreshUrl=None,
    scheme_name=None,
    scopes=None,
    description=None,
    auto_error=True,
)

```

Bases: `OAuth2[](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2 "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.security.OAuth2</span> \(<code>fastapi.security.oauth2.OAuth2</code>\)")`
OAuth2 flow for authentication using a bearer token obtained with an OAuth2 code flow. An instance of it would be used as a dependency.  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `tokenUrl`  |  The URL to obtain the OAuth2 token. **TYPE:** `str`  |  
|  `refreshUrl`  |  The URL to refresh the token and obtain a new one. **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `scopes`  |  The OAuth2 scopes that would be required by the _path operations_ that use this dependency. **TYPE:** `dict[](https://fastapi.tiangolo.com/python-types/#dict "Dict \(<code>dict</code>\)")[str, str] | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if no HTTP Authorization header is provided, required for OAuth2 authentication, it will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the HTTP Authorization header is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, with OAuth2 or in a cookie). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/oauth2.py`

```
def __init__(
    self,
    authorizationUrl: str,
    tokenUrl: Annotated[
        str,
        Doc(
            """
            The URL to obtain the OAuth2 token.
            """
        ),
    ],
    refreshUrl: Annotated[
        str | None,
        Doc(
            """
            The URL to refresh the token and obtain a new one.
            """
        ),
    ] = None,
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    scopes: Annotated[
        dict[str, str] | None,
        Doc(
            """
            The OAuth2 scopes that would be required by the *path operations* that
            use this dependency.
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if no HTTP Authorization header is provided, required for
            OAuth2 authentication, it will automatically cancel the request and
            send the client an error.

            If `auto_error` is set to `False`, when the HTTP Authorization header
            is not available, instead of erroring out, the dependency result will
            be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, with OAuth2
            or in a cookie).
            """
        ),
    ] = True,
):
    if not scopes:
        scopes = {}
    flows = OAuthFlowsModel(
        authorizationCode=cast(
            Any,
            {
                "authorizationUrl": authorizationUrl,
                "tokenUrl": tokenUrl,
                "refreshUrl": refreshUrl,
                "scopes": scopes,
            },
        )
    )
    super().__init__(
        flows=flows,
        scheme_name=scheme_name,
        description=description,
        auto_error=auto_error,
    )

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2AuthorizationCodeBearer.model "Permanent link")

```
model = OAuth2[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuth2 "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuth2</span> \(<code>fastapi.openapi.models.OAuth2</code>\)")(
    flows=cast(OAuthFlows[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuthFlows "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuthFlows</span> \(<code>fastapi.openapi.models.OAuthFlows</code>\)"), flows), description=description
)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2AuthorizationCodeBearer.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2AuthorizationCodeBearer.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2AuthorizationCodeBearer.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

The OAuth 2 specification doesn't define the challenge that should be used, because a `Bearer` token is not really the only option to authenticate.
But declaring any other authentication challenge would be application-specific as it's not defined in the specification.
For practical reasons, this method uses the `Bearer` challenge by default, as it's probably the most common one.
If you are implementing an OAuth2 authentication scheme other than the provided ones in FastAPI (based on bearer tokens), you might want to override this.
Ref: https://datatracker.ietf.org/doc/html/rfc6749
Source code in `fastapi/security/oauth2.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    """
    The OAuth 2 specification doesn't define the challenge that should be used,
    because a `Bearer` token is not really the only option to authenticate.

    But declaring any other authentication challenge would be application-specific
    as it's not defined in the specification.

    For practical reasons, this method uses the `Bearer` challenge by default, as
    it's probably the most common one.

    If you are implementing an OAuth2 authentication scheme other than the provided
    ones in FastAPI (based on bearer tokens), you might want to override this.

    Ref: https://datatracker.ietf.org/doc/html/rfc6749
    """
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

```

##  `` fastapi.security.OAuth2PasswordBearer [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordBearer "Permanent link")

```
OAuth2PasswordBearer(
    tokenUrl,
    scheme_name=None,
    scopes=None,
    description=None,
    auto_error=True,
    refreshUrl=None,
)

```

Bases: `OAuth2[](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2 "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.security.OAuth2</span> \(<code>fastapi.security.oauth2.OAuth2</code>\)")`
OAuth2 flow for authentication using a bearer token obtained with a password. An instance of it would be used as a dependency.
Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `tokenUrl`  |  The URL to obtain the OAuth2 token. This would be the _path operation_ that has `OAuth2PasswordRequestForm` as a dependency. Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str`  |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `scopes`  |  The OAuth2 scopes that would be required by the _path operations_ that use this dependency. Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `dict[](https://fastapi.tiangolo.com/python-types/#dict "Dict \(<code>dict</code>\)")[str, str] | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if no HTTP Authorization header is provided, required for OAuth2 authentication, it will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the HTTP Authorization header is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, with OAuth2 or in a cookie). **TYPE:** `bool` **DEFAULT:** `True`  |  
|  `refreshUrl`  |  The URL to refresh the token and obtain a new one. **TYPE:** `str | None` **DEFAULT:** `None`  |  
Source code in `fastapi/security/oauth2.py`

```
def __init__(
    self,
    tokenUrl: Annotated[
        str,
        Doc(
            """
            The URL to obtain the OAuth2 token. This would be the *path operation*
            that has `OAuth2PasswordRequestForm` as a dependency.

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ],
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    scopes: Annotated[
        dict[str, str] | None,
        Doc(
            """
            The OAuth2 scopes that would be required by the *path operations* that
            use this dependency.

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if no HTTP Authorization header is provided, required for
            OAuth2 authentication, it will automatically cancel the request and
            send the client an error.

            If `auto_error` is set to `False`, when the HTTP Authorization header
            is not available, instead of erroring out, the dependency result will
            be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, with OAuth2
            or in a cookie).
            """
        ),
    ] = True,
    refreshUrl: Annotated[
        str | None,
        Doc(
            """
            The URL to refresh the token and obtain a new one.
            """
        ),
    ] = None,
):
    if not scopes:
        scopes = {}
    flows = OAuthFlowsModel(
        password=cast(
            Any,
            {
                "tokenUrl": tokenUrl,
                "refreshUrl": refreshUrl,
                "scopes": scopes,
            },
        )
    )
    super().__init__(
        flows=flows,
        scheme_name=scheme_name,
        description=description,
        auto_error=auto_error,
    )

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordBearer.model "Permanent link")

```
model = OAuth2[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuth2 "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuth2</span> \(<code>fastapi.openapi.models.OAuth2</code>\)")(
    flows=cast(OAuthFlows[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OAuthFlows "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OAuthFlows</span> \(<code>fastapi.openapi.models.OAuthFlows</code>\)"), flows), description=description
)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordBearer.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordBearer.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordBearer.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

The OAuth 2 specification doesn't define the challenge that should be used, because a `Bearer` token is not really the only option to authenticate.
But declaring any other authentication challenge would be application-specific as it's not defined in the specification.
For practical reasons, this method uses the `Bearer` challenge by default, as it's probably the most common one.
If you are implementing an OAuth2 authentication scheme other than the provided ones in FastAPI (based on bearer tokens), you might want to override this.
Ref: https://datatracker.ietf.org/doc/html/rfc6749
Source code in `fastapi/security/oauth2.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    """
    The OAuth 2 specification doesn't define the challenge that should be used,
    because a `Bearer` token is not really the only option to authenticate.

    But declaring any other authentication challenge would be application-specific
    as it's not defined in the specification.

    For practical reasons, this method uses the `Bearer` challenge by default, as
    it's probably the most common one.

    If you are implementing an OAuth2 authentication scheme other than the provided
    ones in FastAPI (based on bearer tokens), you might want to override this.

    Ref: https://datatracker.ietf.org/doc/html/rfc6749
    """
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

```

## OAuth2 Password Form[¶](https://fastapi.tiangolo.com/reference/security/#oauth2-password-form "Permanent link")
##  `` fastapi.security.OAuth2PasswordRequestForm [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm "Permanent link")

```
OAuth2PasswordRequestForm(
    *,
    grant_type=None,
    username,
    password,
    scope="",
    client_id=None,
    client_secret=None
)

```

This is a dependency class to collect the `username` and `password` as form data for an OAuth2 password flow.
The OAuth2 specification dictates that for a password flow the data should be collected using form data (instead of JSON) and that it should have the specific fields `username` and `password`.
All the initialization parameters are extracted from the request.
Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
#### Example[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm--example "Permanent link")

```
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()


@app.post("/login")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    data = {}
    data["scopes"] = []
    for scope in form_data.scopes:
        data["scopes"].append(scope)
    if form_data.client_id:
        data["client_id"] = form_data.client_id
    if form_data.client_secret:
        data["client_secret"] = form_data.client_secret
    return data

```

Note that for OAuth2 the scope `items:read` is a single scope in an opaque string. You could have custom internal logic to separate it by colon characters (`:`) or similar, and get the two parts `items` and `read`. Many applications do that to group and organize permissions, you could do it as well in your application, just know that it is application specific, it's not part of the specification.  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `grant_type`  |  The OAuth2 spec says it is required and MUST be the fixed string "password". Nevertheless, this dependency class is permissive and allows not passing it. If you want to enforce it, use instead the `OAuth2PasswordRequestFormStrict` dependency. Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `username`  |  `username` string. The OAuth2 spec requires the exact field name `username`. Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str`  |  
|  `password`  |  `password` string. The OAuth2 spec requires the exact field name `password`. Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str`  |  
|  `scope`  |  A single string with actually several scopes separated by spaces. Each scope is also a string. For example, a single string with: ```python "items:read items:write users:read profile openid" ```` would represent the scopes:
  * `items:read`
  * `items:write`
  * `users:read`
  * `profile`
  * `openid`

Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str` **DEFAULT:** `''`  |  
|  `client_id`  |  If there's a `client_id`, it can be sent as part of the form fields. But the OAuth2 specification recommends sending the `client_id` and `client_secret` (if any) using HTTP Basic auth. **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `client_secret`  |  If there's a `client_secret` (and a `client_id`), they can be sent as part of the form fields. But the OAuth2 specification recommends sending the `client_id` and `client_secret` (if any) using HTTP Basic auth. **TYPE:** `str | None` **DEFAULT:** `None`  |  
Source code in `fastapi/security/oauth2.py`

```
def __init__(
    self,
    *,
    grant_type: Annotated[
        str | None,
        Form(pattern="^password$"),
        Doc(
            """
            The OAuth2 spec says it is required and MUST be the fixed string
            "password". Nevertheless, this dependency class is permissive and
            allows not passing it. If you want to enforce it, use instead the
            `OAuth2PasswordRequestFormStrict` dependency.

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ] = None,
    username: Annotated[
        str,
        Form(),
        Doc(
            """
            `username` string. The OAuth2 spec requires the exact field name
            `username`.

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ],
    password: Annotated[
        str,
        Form(json_schema_extra={"format": "password"}),
        Doc(
            """
            `password` string. The OAuth2 spec requires the exact field name
            `password`.

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ],
    scope: Annotated[
        str,
        Form(),
        Doc(
            """
            A single string with actually several scopes separated by spaces. Each
            scope is also a string.

            For example, a single string with:

        ```python
            "items:read items:write users:read profile openid"
        ````

            would represent the scopes:

            * `items:read`
            * `items:write`
            * `users:read`
            * `profile`
            * `openid`

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ] = "",
    client_id: Annotated[
        str | None,
        Form(),
        Doc(
            """
            If there's a `client_id`, it can be sent as part of the form fields.
            But the OAuth2 specification recommends sending the `client_id` and
            `client_secret` (if any) using HTTP Basic auth.
            """
        ),
    ] = None,
    client_secret: Annotated[
        str | None,
        Form(json_schema_extra={"format": "password"}),
        Doc(
            """
            If there's a `client_secret` (and a `client_id`), they can be sent
            as part of the form fields. But the OAuth2 specification recommends
            sending the `client_id` and `client_secret` (if any) using HTTP Basic
            auth.
            """
        ),
    ] = None,
):
    self.grant_type = grant_type
    self.username = username
    self.password = password
    self.scopes = scope.split()
    self.client_id = client_id
    self.client_secret = client_secret

```

###  `` grant_type `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm.grant_type "Permanent link")

```
grant_type = grant_type

```

###  `` username `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm.username "Permanent link")

```
username = username

```

###  `` password `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm.password "Permanent link")

```
password = password

```

###  `` scopes `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm.scopes "Permanent link")

```
scopes = split()

```

###  `` client_id `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm.client_id "Permanent link")

```
client_id = client_id

```

###  `` client_secret `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm.client_secret "Permanent link")

```
client_secret = client_secret

```

##  `` fastapi.security.OAuth2PasswordRequestFormStrict [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestFormStrict "Permanent link")

```
OAuth2PasswordRequestFormStrict(
    grant_type,
    username,
    password,
    scope="",
    client_id=None,
    client_secret=None,
)

```

Bases: `OAuth2PasswordRequestForm[](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestForm "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.security.OAuth2PasswordRequestForm</span> \(<code>fastapi.security.oauth2.OAuth2PasswordRequestForm</code>\)")`
This is a dependency class to collect the `username` and `password` as form data for an OAuth2 password flow.
The OAuth2 specification dictates that for a password flow the data should be collected using form data (instead of JSON) and that it should have the specific fields `username` and `password`.
All the initialization parameters are extracted from the request.
The only difference between `OAuth2PasswordRequestFormStrict` and `OAuth2PasswordRequestForm` is that `OAuth2PasswordRequestFormStrict` requires the client to send the form field `grant_type` with the value `"password"`, which is required in the OAuth2 specification (it seems that for no particular reason), while for `OAuth2PasswordRequestForm` `grant_type` is optional.
Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
#### Example[¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestFormStrict--example "Permanent link")

```
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()


@app.post("/login")
def login(form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()]):
    data = {}
    data["scopes"] = []
    for scope in form_data.scopes:
        data["scopes"].append(scope)
    if form_data.client_id:
        data["client_id"] = form_data.client_id
    if form_data.client_secret:
        data["client_secret"] = form_data.client_secret
    return data

```

Note that for OAuth2 the scope `items:read` is a single scope in an opaque string. You could have custom internal logic to separate it by colon characters (`:`) or similar, and get the two parts `items` and `read`. Many applications do that to group and organize permissions, you could do it as well in your application, just know that it is application specific, it's not part of the specification.
the OAuth2 spec says it is required and MUST be the fixed string "password".
This dependency is strict about it. If you want to be permissive, use instead the OAuth2PasswordRequestForm dependency class.
username: username string. The OAuth2 spec requires the exact field name "username". password: password string. The OAuth2 spec requires the exact field name "password". scope: Optional string. Several scopes (each one a string) separated by spaces. E.g. "items:read items:write users:read profile openid" client_id: optional string. OAuth2 recommends sending the client_id and client_secret (if any) using HTTP Basic auth, as: client_id:client_secret client_secret: optional string. OAuth2 recommends sending the client_id and client_secret (if any) using HTTP Basic auth, as: client_id:client_secret  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `grant_type`  |  The OAuth2 spec says it is required and MUST be the fixed string "password". This dependency is strict about it. If you want to be permissive, use instead the `OAuth2PasswordRequestForm` dependency class. Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str`  |  
|  `username`  |  `username` string. The OAuth2 spec requires the exact field name `username`. Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str`  |  
|  `password`  |  `password` string. The OAuth2 spec requires the exact field name `password`. Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str`  |  
|  `scope`  |  A single string with actually several scopes separated by spaces. Each scope is also a string. For example, a single string with: ```python "items:read items:write users:read profile openid" ```` would represent the scopes:
  * `items:read`
  * `items:write`
  * `users:read`
  * `profile`
  * `openid`

Read more about it in the [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/). **TYPE:** `str` **DEFAULT:** `''`  |  
|  `client_id`  |  If there's a `client_id`, it can be sent as part of the form fields. But the OAuth2 specification recommends sending the `client_id` and `client_secret` (if any) using HTTP Basic auth. **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `client_secret`  |  If there's a `client_secret` (and a `client_id`), they can be sent as part of the form fields. But the OAuth2 specification recommends sending the `client_id` and `client_secret` (if any) using HTTP Basic auth. **TYPE:** `str | None` **DEFAULT:** `None`  |  
Source code in `fastapi/security/oauth2.py`

```
def __init__(
    self,
    grant_type: Annotated[
        str,
        Form(pattern="^password$"),
        Doc(
            """
            The OAuth2 spec says it is required and MUST be the fixed string
            "password". This dependency is strict about it. If you want to be
            permissive, use instead the `OAuth2PasswordRequestForm` dependency
            class.

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ],
    username: Annotated[
        str,
        Form(),
        Doc(
            """
            `username` string. The OAuth2 spec requires the exact field name
            `username`.

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ],
    password: Annotated[
        str,
        Form(),
        Doc(
            """
            `password` string. The OAuth2 spec requires the exact field name
            `password`.

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ],
    scope: Annotated[
        str,
        Form(),
        Doc(
            """
            A single string with actually several scopes separated by spaces. Each
            scope is also a string.

            For example, a single string with:

        ```python
            "items:read items:write users:read profile openid"
        ````

            would represent the scopes:

            * `items:read`
            * `items:write`
            * `users:read`
            * `profile`
            * `openid`

            Read more about it in the
            [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
            """
        ),
    ] = "",
    client_id: Annotated[
        str | None,
        Form(),
        Doc(
            """
            If there's a `client_id`, it can be sent as part of the form fields.
            But the OAuth2 specification recommends sending the `client_id` and
            `client_secret` (if any) using HTTP Basic auth.
            """
        ),
    ] = None,
    client_secret: Annotated[
        str | None,
        Form(),
        Doc(
            """
            If there's a `client_secret` (and a `client_id`), they can be sent
            as part of the form fields. But the OAuth2 specification recommends
            sending the `client_id` and `client_secret` (if any) using HTTP Basic
            auth.
            """
        ),
    ] = None,
):
    super().__init__(
        grant_type=grant_type,
        username=username,
        password=password,
        scope=scope,
        client_id=client_id,
        client_secret=client_secret,
    )

```

###  `` grant_type `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestFormStrict.grant_type "Permanent link")

```
grant_type = grant_type

```

###  `` username `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestFormStrict.username "Permanent link")

```
username = username

```

###  `` password `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestFormStrict.password "Permanent link")

```
password = password

```

###  `` scopes `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestFormStrict.scopes "Permanent link")

```
scopes = split()

```

###  `` client_id `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestFormStrict.client_id "Permanent link")

```
client_id = client_id

```

###  `` client_secret `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OAuth2PasswordRequestFormStrict.client_secret "Permanent link")

```
client_secret = client_secret

```

## OAuth2 Security Scopes in Dependencies[¶](https://fastapi.tiangolo.com/reference/security/#oauth2-security-scopes-in-dependencies "Permanent link")
##  `` fastapi.security.SecurityScopes [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.SecurityScopes "Permanent link")

```
SecurityScopes(scopes=None)

```

This is a special class that you can define in a parameter in a dependency to obtain the OAuth2 scopes required by all the dependencies in the same chain.
This way, multiple dependencies can have different scopes, even when used in the same _path operation_. And with this, you can access all the scopes required in all those dependencies in a single place.
Read more about it in the [FastAPI docs for OAuth2 scopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/).  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `scopes`  |  This will be filled by FastAPI. **TYPE:** `list[](https://fastapi.tiangolo.com/python-types/#list "List \(<code>list</code>\)")[str] | None` **DEFAULT:** `None`  |  
Source code in `fastapi/security/oauth2.py`

```
def __init__(
    self,
    scopes: Annotated[
        list[str] | None,
        Doc(
            """
            This will be filled by FastAPI.
            """
        ),
    ] = None,
):
    self.scopes: Annotated[
        list[str],
        Doc(
            """
            The list of all the scopes required by dependencies.
            """
        ),
    ] = scopes or []
    self.scope_str: Annotated[
        str,
        Doc(
            """
            All the scopes required by all the dependencies in a single string
            separated by spaces, as defined in the OAuth2 specification.
            """
        ),
    ] = " ".join(self.scopes)

```

###  `` scopes `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.SecurityScopes.scopes "Permanent link")

```
scopes = scopes or []

```

The list of all the scopes required by dependencies.
###  `` scope_str `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.SecurityScopes.scope_str "Permanent link")

```
scope_str = join(scopes)

```

All the scopes required by all the dependencies in a single string separated by spaces, as defined in the OAuth2 specification.
## OpenID Connect[¶](https://fastapi.tiangolo.com/reference/security/#openid-connect "Permanent link")
##  `` fastapi.security.OpenIdConnect [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OpenIdConnect "Permanent link")

```
OpenIdConnect(
    *,
    openIdConnectUrl,
    scheme_name=None,
    description=None,
    auto_error=True
)

```

Bases: `SecurityBase`
OpenID Connect authentication class. An instance of it would be used as a dependency.
**Warning** : this is only a stub to connect the components with OpenAPI in FastAPI, but it doesn't implement the full OpenIdConnect scheme, for example, it doesn't use the OpenIDConnect URL. You would need to subclass it and implement it in your code.  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `openIdConnectUrl`  |  The OpenID Connect URL. **TYPE:** `str`  |  
|  `scheme_name`  |  Security scheme name. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `description`  |  Security scheme description. It will be included in the generated OpenAPI (e.g. visible at `/docs`). **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `auto_error`  |  By default, if no HTTP Authorization header is provided, required for OpenID Connect authentication, it will automatically cancel the request and send the client an error. If `auto_error` is set to `False`, when the HTTP Authorization header is not available, instead of erroring out, the dependency result will be `None`. This is useful when you want to have optional authentication. It is also useful when you want to have authentication that can be provided in one of multiple optional ways (for example, with OpenID Connect or in a cookie). **TYPE:** `bool` **DEFAULT:** `True`  |  
Source code in `fastapi/security/open_id_connect_url.py`

```
def __init__(
    self,
    *,
    openIdConnectUrl: Annotated[
        str,
        Doc(
            """
        The OpenID Connect URL.
        """
        ),
    ],
    scheme_name: Annotated[
        str | None,
        Doc(
            """
            Security scheme name.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    description: Annotated[
        str | None,
        Doc(
            """
            Security scheme description.

            It will be included in the generated OpenAPI (e.g. visible at `/docs`).
            """
        ),
    ] = None,
    auto_error: Annotated[
        bool,
        Doc(
            """
            By default, if no HTTP Authorization header is provided, required for
            OpenID Connect authentication, it will automatically cancel the request
            and send the client an error.

            If `auto_error` is set to `False`, when the HTTP Authorization header
            is not available, instead of erroring out, the dependency result will
            be `None`.

            This is useful when you want to have optional authentication.

            It is also useful when you want to have authentication that can be
            provided in one of multiple optional ways (for example, with OpenID
            Connect or in a cookie).
            """
        ),
    ] = True,
):
    self.model = OpenIdConnectModel(
        openIdConnectUrl=openIdConnectUrl, description=description
    )
    self.scheme_name = scheme_name or self.__class__.__name__
    self.auto_error = auto_error

```

###  `` model `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OpenIdConnect.model "Permanent link")

```
model = OpenIdConnect[](https://fastapi.tiangolo.com/reference/openapi/models/#fastapi.openapi.models.OpenIdConnect "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">OpenIdConnect</span> \(<code>fastapi.openapi.models.OpenIdConnect</code>\)")(
    openIdConnectUrl=openIdConnectUrl,
    description=description,
)

```

###  `` scheme_name `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OpenIdConnect.scheme_name "Permanent link")

```
scheme_name = scheme_name or __name__

```

###  `` auto_error `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OpenIdConnect.auto_error "Permanent link")

```
auto_error = auto_error

```

###  `` make_not_authenticated_error [¶](https://fastapi.tiangolo.com/reference/security/#fastapi.security.OpenIdConnect.make_not_authenticated_error "Permanent link")

```
make_not_authenticated_error()

```

Source code in `fastapi/security/open_id_connect_url.py`

```
def make_not_authenticated_error(self) -> HTTPException:
    return HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

```

