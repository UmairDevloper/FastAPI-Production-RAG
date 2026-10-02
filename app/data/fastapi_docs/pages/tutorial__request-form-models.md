# Form Models - FastAPI

Source: https://fastapi.tiangolo.com/tutorial/request-form-models/

# Form Models[¶](https://fastapi.tiangolo.com/tutorial/request-form-models/#form-models "Permanent link")
You can use **Pydantic models** to declare **form fields** in FastAPI.
Note
To use forms, first install [`python-multipart`](https://github.com/Kludex/python-multipart).
Add it to your project:

```
$ uv add python-multipart

```

Note
This is supported since FastAPI version `0.113.0`. 🤓
## Pydantic Models for Forms[¶](https://fastapi.tiangolo.com/tutorial/request-form-models/#pydantic-models-for-forms "Permanent link")
You just need to declare a **Pydantic model** with the fields you want to receive as **form fields** , and then declare the parameter as `Form`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/request-form-models/#__tabbed_1_1)

```
from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()


class FormData(BaseModel):
    username: str
    password: str


@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/request-form-models/#__tabbed_2_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()


class FormData(BaseModel):
    username: str
    password: str


@app.post("/login/")
async def login(data: FormData = Form()):
    return data

```

**FastAPI** will **extract** the data for **each field** from the **form data** in the request and give you the Pydantic model you defined.
## Check the Docs[¶](https://fastapi.tiangolo.com/tutorial/request-form-models/#check-the-docs "Permanent link")
You can verify it in the docs UI at `/docs`:
![](https://fastapi.tiangolo.com/img/tutorial/request-form-models/image01.png)
## Forbid Extra Form Fields[¶](https://fastapi.tiangolo.com/tutorial/request-form-models/#forbid-extra-form-fields "Permanent link")
In some special use cases (probably not very common), you might want to **restrict** the form fields to only those declared in the Pydantic model. And **forbid** any **extra** fields.
Note
This is supported since FastAPI version `0.114.0`. 🤓
You can use Pydantic's model configuration to `forbid` any `extra` fields:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/request-form-models/#__tabbed_3_1)

```
from typing import Annotated

from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()


class FormData(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}


@app.post("/login/")
async def login(data: Annotated[FormData, Form()]):
    return data

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/request-form-models/#__tabbed_4_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()


class FormData(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}


@app.post("/login/")
async def login(data: FormData = Form()):
    return data

```

If a client tries to send some extra data, they will receive an **error** response.
For example, if the client tries to send the form fields:
  * `username`: `Rick`
  * `password`: `Portal Gun`
  * `extra`: `Mr. Poopybutthole`


They will receive an error response telling them that the field `extra` is not allowed:

```
{
    "detail": [
        {
            "type": "extra_forbidden",
            "loc": ["body", "extra"],
            "msg": "Extra inputs are not permitted",
            "input": "Mr. Poopybutthole"
        }
    ]
}

```

## Summary[¶](https://fastapi.tiangolo.com/tutorial/request-form-models/#summary "Permanent link")
You can use Pydantic models to declare form fields in FastAPI. 😎
