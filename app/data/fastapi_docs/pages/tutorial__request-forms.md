# Form Data - FastAPI

Source: https://fastapi.tiangolo.com/tutorial/request-forms/

# Form Data[¶](https://fastapi.tiangolo.com/tutorial/request-forms/#form-data "Permanent link")
When you need to receive form fields instead of JSON, you can use `Form`.
Note
To use forms, first install [`python-multipart`](https://github.com/Kludex/python-multipart).
Add it to your project:

```
$ uv add python-multipart

```

## Import `Form`[¶](https://fastapi.tiangolo.com/tutorial/request-forms/#import-form "Permanent link")
Import `Form` from `fastapi`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/request-forms/#__tabbed_1_1)

```
from typing import Annotated

from fastapi import FastAPI, Form

app = FastAPI()


@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/request-forms/#__tabbed_2_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import FastAPI, Form

app = FastAPI()


@app.post("/login/")
async def login(username: str = Form(), password: str = Form()):
    return {"username": username}

```

## Define `Form` parameters[¶](https://fastapi.tiangolo.com/tutorial/request-forms/#define-form-parameters "Permanent link")
Create form parameters the same way you would for `Body` or `Query`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/request-forms/#__tabbed_3_1)

```
from typing import Annotated

from fastapi import FastAPI, Form

app = FastAPI()


@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/request-forms/#__tabbed_4_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import FastAPI, Form

app = FastAPI()


@app.post("/login/")
async def login(username: str = Form(), password: str = Form()):
    return {"username": username}

```

For example, in one of the ways the OAuth2 specification can be used (called "password flow") it is required to send a `username` and `password` as form fields.
The spec requires the fields to be exactly named `username` and `password`, and to be sent as form fields, not JSON.
With `Form` you can declare the same configurations as with `Body` (and `Query`, `Path`, `Cookie`), including validation, examples, an alias (e.g. `user-name` instead of `username`), etc.
Note
`Form` is a class that inherits directly from `Body`.
Tip
To declare form bodies, you need to use `Form` explicitly, because without it the parameters would be interpreted as query parameters or body (JSON) parameters.
## About "Form Fields"[¶](https://fastapi.tiangolo.com/tutorial/request-forms/#about-form-fields "Permanent link")
The way HTML forms (`<form></form>`) send the data to the server normally uses a "special" encoding for that data, it's different from JSON.
**FastAPI** will make sure to read that data from the right place instead of JSON.
Technical Details
Data from forms is normally encoded using the "media type" `application/x-www-form-urlencoded`.
But when the form includes files, it is encoded as `multipart/form-data`. You'll read about handling files in the next chapter.
If you want to read more about these encodings and form fields, head to the [MDN web docs for `POST`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST).
Warning
You can declare multiple `Form` parameters in a _path operation_ , but you can't also declare `Body` fields that you expect to receive as JSON, as the request will have the body encoded using `application/x-www-form-urlencoded` instead of `application/json`.
This is not a limitation of **FastAPI** , it's part of the HTTP protocol.
## Recap[¶](https://fastapi.tiangolo.com/tutorial/request-forms/#recap "Permanent link")
Use `Form` to declare form data input parameters.
  *[MDN]: Mozilla Developer Network
