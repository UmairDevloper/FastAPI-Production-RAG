# Templating - Jinja2Templates - FastAPI

Source: https://fastapi.tiangolo.com/reference/templating/

# Templating - `Jinja2Templates`[¶](https://fastapi.tiangolo.com/reference/templating/#templating-jinja2templates "Permanent link")
You can use the `Jinja2Templates` class to render Jinja templates.
Read more about it in the [FastAPI docs for Templates](https://fastapi.tiangolo.com/advanced/templates/).
You can import it directly from `fastapi.templating`:

```
from fastapi.templating import Jinja2Templates

```

##  `` fastapi.templating.Jinja2Templates [¶](https://fastapi.tiangolo.com/reference/templating/#fastapi.templating.Jinja2Templates "Permanent link")

```
Jinja2Templates(
    directory: (
        str | PathLike[str] | Sequence[str | PathLike[str]]
    ),
    *,
    context_processors: (
        list[](https://fastapi.tiangolo.com/python-types/#list "List \(<code>list</code>\)")[Callable[[Request[](https://fastapi.tiangolo.com/reference/request/#fastapi.Request "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.Request</span> \(<code>starlette.requests.Request</code>\)")], dict[](https://fastapi.tiangolo.com/python-types/#dict "Dict \(<code>dict</code>\)")[str, Any]]] | None
    ) = None
)

```


```
Jinja2Templates(
    *,
    env: Environment,
    context_processors: (
        list[](https://fastapi.tiangolo.com/python-types/#list "List \(<code>list</code>\)")[Callable[[Request[](https://fastapi.tiangolo.com/reference/request/#fastapi.Request "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.Request</span> \(<code>starlette.requests.Request</code>\)")], dict[](https://fastapi.tiangolo.com/python-types/#dict "Dict \(<code>dict</code>\)")[str, Any]]] | None
    ) = None
)

```


```
Jinja2Templates(
    directory=None, *, context_processors=None, env=None
)

```

Jinja2 template renderer.
Example

```
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

async def homepage(request: Request) -> Response:
    return templates.TemplateResponse(request, "index.html")

```

Source code in `starlette/templating.py`

```
def __init__(
    self,
    directory: str | PathLike[str] | Sequence[str | PathLike[str]] | None = None,
    *,
    context_processors: list[Callable[[Request], dict[str, Any]]] | None = None,
    env: jinja2.Environment | None = None,
) -> None:
    assert bool(directory) ^ bool(env), "either 'directory' or 'env' arguments must be passed"
    self.context_processors = context_processors or []
    if directory is not None:
        loader = jinja2.FileSystemLoader(directory)
        self.env = jinja2.Environment(loader=loader, autoescape=jinja2.select_autoescape())
    elif env is not None:  # pragma: no branch
        self.env = env

    self._setup_env_defaults(self.env)

```

###  `` context_processors `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/templating/#fastapi.templating.Jinja2Templates.context_processors "Permanent link")

```
context_processors = context_processors or []

```

###  `` env `instance-attribute` [¶](https://fastapi.tiangolo.com/reference/templating/#fastapi.templating.Jinja2Templates.env "Permanent link")

```
env = Environment(
    loader=loader, autoescape=select_autoescape()
)

```

###  `` get_template [¶](https://fastapi.tiangolo.com/reference/templating/#fastapi.templating.Jinja2Templates.get_template "Permanent link")

```
get_template(name)

```

Source code in `starlette/templating.py`

```
def get_template(self, name: str) -> jinja2.Template:
    return self.env.get_template(name)

```

###  `` TemplateResponse [¶](https://fastapi.tiangolo.com/reference/templating/#fastapi.templating.Jinja2Templates.TemplateResponse "Permanent link")

```
TemplateResponse(
    request,
    name,
    context=None,
    status_code=200,
    headers=None,
    media_type=None,
    background=None,
)

```

Render a template and return an HTML response.  
| PARAMETER  | DESCRIPTION  |  
| --- | --- |  
|  `request`  |  The incoming request instance. **TYPE:** `Request[](https://fastapi.tiangolo.com/reference/request/#fastapi.Request "<code class="doc-symbol doc-symbol-heading doc-symbol-class"></code>            <span class="doc doc-object-name doc-class-name">fastapi.Request</span> \(<code>starlette.requests.Request</code>\)")`  |  
|  `name`  |  The template file name to render. **TYPE:** `str`  |  
|  `context`  |  Variables to pass to the template. **TYPE:** `dict[](https://fastapi.tiangolo.com/python-types/#dict "Dict \(<code>dict</code>\)")[str, Any] | None` **DEFAULT:** `None`  |  
|  `status_code`  |  HTTP status code for the response. **TYPE:** `int` **DEFAULT:** `200`  |  
|  `headers`  |  Additional headers to include in the response. **TYPE:** `Mapping[str, str] | None` **DEFAULT:** `None`  |  
|  `media_type`  |  Media type for the response. **TYPE:** `str | None` **DEFAULT:** `None`  |  
|  `background`  |  Background task to run after response is sent. **TYPE:** `BackgroundTask | None` **DEFAULT:** `None`  |  
| RETURNS  | DESCRIPTION  |  
| --- | --- |  
|  `_TemplateResponse`  |  An HTML response with the rendered template content.  |  
Source code in `starlette/templating.py`

```
def TemplateResponse(
    self,
    request: Request,
    name: str,
    context: dict[str, Any] | None = None,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
) -> _TemplateResponse:
    """
    Render a template and return an HTML response.

    Args:
        request: The incoming request instance.
        name: The template file name to render.
        context: Variables to pass to the template.
        status_code: HTTP status code for the response.
        headers: Additional headers to include in the response.
        media_type: Media type for the response.
        background: Background task to run after response is sent.

    Returns:
        An HTML response with the rendered template content.
    """
    context = context or {}

    context.setdefault("request", request)
    for context_processor in self.context_processors:
        context.update(context_processor(request))

    template = self.get_template(name)
    return _TemplateResponse(
        template,
        context,
        status_code=status_code,
        headers=headers,
        media_type=media_type,
        background=background,
    )

```

