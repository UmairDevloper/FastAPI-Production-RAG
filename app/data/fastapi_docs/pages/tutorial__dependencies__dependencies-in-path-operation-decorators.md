# Dependencies in path operation decorators - FastAPI

Source: https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/

# Dependencies in path operation decorators[¶](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#dependencies-in-path-operation-decorators "Permanent link")
In some cases you don't really need the return value of a dependency inside your _path operation function_.
Or the dependency doesn't return a value.
But you still need it to be executed/solved.
For those cases, instead of declaring a _path operation function_ parameter with `Depends`, you can add a `list` of `dependencies` to the _path operation decorator_.
## Add `dependencies` to the _path operation decorator_[¶](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#add-dependencies-to-the-path-operation-decorator "Permanent link")
The _path operation decorator_ receives an optional argument `dependencies`.
It should be a `list` of `Depends()`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#__tabbed_1_1)

```
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#__tabbed_2_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


async def verify_token(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: str = Header()):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

```

These dependencies will be executed/solved the same way as normal dependencies. But their value (if they return any) won't be passed to your _path operation function_.
Tip
Some editors check for unused function parameters, and show them as errors.
Using these `dependencies` in the _path operation decorator_ you can make sure they are executed while avoiding editor/tooling errors.
It might also help avoid confusion for new developers that see an unused parameter in your code and could think it's unnecessary.
Note
In this example we use invented custom headers `X-Key` and `X-Token`.
But in real cases, when implementing security, you would get more benefits from using the integrated [Security utilities (the next chapter)](https://fastapi.tiangolo.com/tutorial/security/).
## Dependencies errors and return values[¶](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#dependencies-errors-and-return-values "Permanent link")
You can use the same dependency _functions_ you use normally.
### Dependency requirements[¶](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#dependency-requirements "Permanent link")
They can declare request requirements (like headers) or other sub-dependencies:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#__tabbed_3_1)

```
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#__tabbed_4_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


async def verify_token(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: str = Header()):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

```

### Raise exceptions[¶](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#raise-exceptions "Permanent link")
These dependencies can `raise` exceptions, the same as normal dependencies:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#__tabbed_5_1)

```
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#__tabbed_6_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


async def verify_token(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: str = Header()):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

```

### Return values[¶](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#return-values "Permanent link")
And they can return values or not, the values won't be used.
So, you can reuse a normal dependency (that returns a value) you already use somewhere else, and even though the value won't be used, the dependency will be executed:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#__tabbed_7_1)

```
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

```

🤓 Other versions and variants
[Python 3.10+ - non-Annotated](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#__tabbed_8_1)
Tip
Prefer to use the `Annotated` version if possible.

```
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


async def verify_token(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: str = Header()):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]

```

## Dependencies for a group of _path operations_[¶](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#dependencies-for-a-group-of-path-operations "Permanent link")
Later, when reading about how to structure bigger applications ([Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)), possibly with multiple files, you will learn how to declare a single `dependencies` parameter for a group of _path operations_.
## Global Dependencies[¶](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/#global-dependencies "Permanent link")
Next we will see how to add dependencies to the whole `FastAPI` application, so that they apply to each _path operation_.
