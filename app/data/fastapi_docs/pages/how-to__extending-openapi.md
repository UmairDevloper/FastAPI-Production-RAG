# Extending OpenAPI - FastAPI

Source: https://fastapi.tiangolo.com/how-to/extending-openapi/

# Extending OpenAPI[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#extending-openapi "Permanent link")
There are some cases where you might need to modify the generated OpenAPI schema.
In this section you will see how.
## The normal process[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#the-normal-process "Permanent link")
The normal (default) process, is as follows.
A `FastAPI` application (instance) has an `.openapi()` method that is expected to return the OpenAPI schema.
As part of the application object creation, a _path operation_ for `/openapi.json` (or for whatever you set your `openapi_url`) is registered.
It just returns a JSON response with the result of the application's `.openapi()` method.
By default, what the method `.openapi()` does is check the property `.openapi_schema` to see if it has contents and return them.
If it doesn't, it generates them using the utility function at `fastapi.openapi.utils.get_openapi`.
And that function `get_openapi()` receives as parameters:
  * `title`: The OpenAPI title, shown in the docs.
  * `version`: The version of your API, e.g. `2.5.0`.
  * `openapi_version`: The version of the OpenAPI specification used. By default, the latest: `3.1.0`.
  * `summary`: A short summary of the API.
  * `description`: The description of your API, this can include markdown and will be shown in the docs.
  * `routes`: The routes from the application, taken from `app.routes`. FastAPI uses them to collect the registered _path operations_ , including those from included routers.


Technical Details
`app.routes` is a lower-level route tree. It can include route candidates that FastAPI uses internally for included routers, not only final `APIRoute` objects.
You can still pass `app.routes` to `get_openapi()`. FastAPI will traverse that route tree to collect the effective path operations.
Note
The parameter `summary` is available in OpenAPI 3.1.0 and above, supported by FastAPI 0.99.0 and above.
## Overriding the defaults[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#overriding-the-defaults "Permanent link")
Using the information above, you can use the same utility function to generate the OpenAPI schema and override each part that you need.
For example, let's add [ReDoc's OpenAPI extension to include a custom logo](https://github.com/Redocly/redoc/blob/main/docs/redoc-vendor-extensions.md#x-logo).
### Normal **FastAPI**[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#normal-fastapi "Permanent link")
First, write all your **FastAPI** application as normally:
[Python 3.10+](https://fastapi.tiangolo.com/how-to/extending-openapi/#__tabbed_1_1)

```
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()


@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

```

### Generate the OpenAPI schema[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#generate-the-openapi-schema "Permanent link")
Then, use the same utility function to generate the OpenAPI schema, inside a `custom_openapi()` function:
[Python 3.10+](https://fastapi.tiangolo.com/how-to/extending-openapi/#__tabbed_2_1)

```
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()


@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

```

### Modify the OpenAPI schema[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#modify-the-openapi-schema "Permanent link")
Now you can add the ReDoc extension, adding a custom `x-logo` to the `info` "object" in the OpenAPI schema:
[Python 3.10+](https://fastapi.tiangolo.com/how-to/extending-openapi/#__tabbed_3_1)

```
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()


@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

```

### Cache the OpenAPI schema[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#cache-the-openapi-schema "Permanent link")
You can use the property `.openapi_schema` as a "cache", to store your generated schema.
That way, your application won't have to generate the schema every time a user opens your API docs.
It will be generated only once, and then the same cached schema will be used for the next requests.
[Python 3.10+](https://fastapi.tiangolo.com/how-to/extending-openapi/#__tabbed_4_1)

```
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()


@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

```

### Override the method[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#override-the-method "Permanent link")
Now you can replace the `.openapi()` method with your new function.
[Python 3.10+](https://fastapi.tiangolo.com/how-to/extending-openapi/#__tabbed_5_1)

```
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()


@app.get("/items/")
async def read_items():
    return [{"name": "Foo"}]


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        summary="This is a very custom OpenAPI schema",
        description="Here's a longer description of the custom **OpenAPI** schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

```

### Check it[¶](https://fastapi.tiangolo.com/how-to/extending-openapi/#check-it "Permanent link")
Once you go to <http://127.0.0.1:8000/redoc> you will see that you are using your custom logo (in this example, **FastAPI** 's logo):
![](https://fastapi.tiangolo.com/img/tutorial/extending-openapi/image01.png)
