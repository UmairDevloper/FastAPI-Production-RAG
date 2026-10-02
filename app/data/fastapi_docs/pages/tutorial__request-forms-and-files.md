# Request Forms and Files - FastAPI

Source: https://fastapi.tiangolo.com/tutorial/request-forms-and-files/

# Request Forms and Files[¶](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#request-forms-and-files "Permanent link")
You can define files and form fields at the same time using `File` and `Form`.
Note
To receive uploaded files and/or form data, first install [`python-multipart`](https://github.com/Kludex/python-multipart).
Add it to your project:

```
$ uv add python-multipart

```

## Import `File` and `Form`[¶](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#import-file-and-form "Permanent link")
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#__tabbed_1_1)

```
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()


@app.post("/files/")
async def create_file(
    file: Annotated[bytes, File()],
    fileb: Annotated[UploadFile, File()],
    token: Annotated[str, Form()],
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#__tabbed_2_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()


@app.post("/files/")
async def create_file(
    file: bytes = File(), fileb: UploadFile = File(), token: str = Form()
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }

```

## Define `File` and `Form` parameters[¶](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#define-file-and-form-parameters "Permanent link")
Create file and form parameters the same way you would for `Body` or `Query`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#__tabbed_3_1)

```
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()


@app.post("/files/")
async def create_file(
    file: Annotated[bytes, File()],
    fileb: Annotated[UploadFile, File()],
    token: Annotated[str, Form()],
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#__tabbed_4_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()


@app.post("/files/")
async def create_file(
    file: bytes = File(), fileb: UploadFile = File(), token: str = Form()
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }

```

The files and form fields will be uploaded as form data and you will receive the files and form fields.
And you can declare some of the files as `bytes` and some as `UploadFile`.
Warning
You can declare multiple `File` and `Form` parameters in a _path operation_ , but you can't also declare `Body` fields that you expect to receive as JSON, as the request will have the body encoded using `multipart/form-data` instead of `application/json`.
This is not a limitation of **FastAPI** , it's part of the HTTP protocol.
## Recap[¶](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#recap "Permanent link")
Use `File` and `Form` together when you need to receive data and files in the same request.
