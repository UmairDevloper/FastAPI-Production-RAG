# Query Parameter Models - FastAPI

Source: https://fastapi.tiangolo.com/tutorial/query-param-models/

# Query Parameter Models[¶](https://fastapi.tiangolo.com/tutorial/query-param-models/#query-parameter-models "Permanent link")
If you have a group of **query parameters** that are related, you can create a **Pydantic model** to declare them.
This would allow you to **re-use the model** in **multiple places** and also to declare validations and metadata for all the parameters at once. 😎
Note
This is supported since FastAPI version `0.115.0`. 🤓
## Query Parameters with a Pydantic Model[¶](https://fastapi.tiangolo.com/tutorial/query-param-models/#query-parameters-with-a-pydantic-model "Permanent link")
Declare the **query parameters** that you need in a **Pydantic model** , and then declare the parameter as `Query`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/query-param-models/#__tabbed_1_1)

```
from typing import Annotated, Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()


class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/query-param-models/#__tabbed_2_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from typing import Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()


class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


@app.get("/items/")
async def read_items(filter_query: FilterParams = Query()):
    return filter_query

```

**FastAPI** will **extract** the data for **each field** from the **query parameters** in the request and give you the Pydantic model you defined.
## Check the Docs[¶](https://fastapi.tiangolo.com/tutorial/query-param-models/#check-the-docs "Permanent link")
You can see the query parameters in the docs UI at `/docs`:
![](https://fastapi.tiangolo.com/img/tutorial/query-param-models/image01.png)
## Forbid Extra Query Parameters[¶](https://fastapi.tiangolo.com/tutorial/query-param-models/#forbid-extra-query-parameters "Permanent link")
In some special use cases (probably not very common), you might want to **restrict** the query parameters that you want to receive.
You can use Pydantic's model configuration to `forbid` any `extra` fields:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/query-param-models/#__tabbed_3_1)

```
from typing import Annotated, Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()


class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/query-param-models/#__tabbed_4_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from typing import Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()


class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


@app.get("/items/")
async def read_items(filter_query: FilterParams = Query()):
    return filter_query

```

If a client tries to send some **extra** data in the **query parameters** , they will receive an **error** response.
For example, if the client tries to send a `tool` query parameter with a value of `plumbus`, like:

```
https://example.com/items/?limit=10&tool=plumbus

```

They will receive an **error** response telling them that the query parameter `tool` is not allowed:

```
{
    "detail": [
        {
            "type": "extra_forbidden",
            "loc": ["query", "tool"],
            "msg": "Extra inputs are not permitted",
            "input": "plumbus"
        }
    ]
}

```

## Summary[¶](https://fastapi.tiangolo.com/tutorial/query-param-models/#summary "Permanent link")
You can use **Pydantic models** to declare **query parameters** in **FastAPI**. 😎
Tip
Spoiler alert: you can also use Pydantic models to declare cookies and headers, but you will read about that later in the tutorial. 🤫
