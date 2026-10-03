# FastAPI CLI - FastAPI

Source: https://fastapi.tiangolo.com/fastapi-cli/

# FastAPI CLI[¶](https://fastapi.tiangolo.com/fastapi-cli/#fastapi-cli "Permanent link")
**FastAPI CLI** is a command line program that you can use to serve your FastAPI app, manage your FastAPI project, and more.
When you add FastAPI to your project (e.g. with `uv add "fastapi[standard]"`), it comes with a command line program you can run in the terminal.
To run your FastAPI app for development, you can use the `fastapi dev` command:

```
<font color="#4E9A06">fastapi</font> dev

fast →fasta


```

Tip
For production you would use `fastapi run` instead of `fastapi dev`. 🚀
Internally, **FastAPI CLI** uses [Uvicorn](https://uvicorn.dev), a high-performance, production-ready, ASGI server. 😎
The `fastapi` CLI will try to detect automatically the FastAPI app to run, assuming it's an object called `app` in a file `main.py` (or a couple other variants).
But you can configure explicitly the app to use.
## Configure the app `entrypoint` in `pyproject.toml`[¶](https://fastapi.tiangolo.com/fastapi-cli/#configure-the-app-entrypoint-in-pyproject-toml "Permanent link")
You can configure where your app is located in a `pyproject.toml` file like:

```
[tool.fastapi]
entrypoint = "main:app"

```

That `entrypoint` will tell the `fastapi` command that it should import the app like:

```
from main import app

```

If your code was structured like:

```
.
├── backend
│   ├── main.py
│   ├── __init__.py

```

Then you would set the `entrypoint` as:

```
[tool.fastapi]
entrypoint = "backend.main:app"

```

which would be equivalent to:

```
from backend.main import app

```

###  `fastapi dev` with path or with `--entrypoint` CLI option[¶](https://fastapi.tiangolo.com/fastapi-cli/#fastapi-dev-with-path-or-with-entrypoint-cli-option "Permanent link")
You can also pass the file path to the `fastapi dev` command, and it will guess the FastAPI app object to use:

```
$ uv run fastapi dev main.py

```

Or, you can also pass the `--entrypoint` option to the `fastapi dev` command:

```
$ uv run fastapi dev --entrypoint main:app

```

But you would have to remember to pass the correct path\entrypoint every time you call the `fastapi` command.
Additionally, other tools might not be able to find it, for example the [VS Code Extension](https://fastapi.tiangolo.com/editor-support/) or [FastAPI Cloud](https://fastapicloud.com), so it is recommended to use the `entrypoint` in `pyproject.toml`.
##  `fastapi dev`[¶](https://fastapi.tiangolo.com/fastapi-cli/#fastapi-dev "Permanent link")
Running `fastapi dev` initiates development mode.
By default, **auto-reload** is enabled, automatically reloading the server when you make changes to your code. This is resource-intensive and could be less stable than when it's disabled. You should only use it for development. It also listens on the IP address `127.0.0.1`, which is the IP for your machine to communicate with itself alone (`localhost`).
Before importing your app, `fastapi dev` sets the `FASTAPI_ENV` environment variable to `development`. If `FASTAPI_ENV` is already set, its existing value is preserved. This lets app startup code choose development-friendly behavior while allowing you to provide an app-specific environment such as `staging`.
The conventional `FASTAPI_ENV` values are `development` and `production`. `fastapi run` currently leaves `FASTAPI_ENV` unchanged, so set it explicitly if your app needs to detect production mode.
##  `fastapi run`[¶](https://fastapi.tiangolo.com/fastapi-cli/#fastapi-run "Permanent link")
Executing `fastapi run` starts FastAPI in production mode.
By default, **auto-reload** is disabled. It also listens on the IP address `0.0.0.0`, which means all the available IP addresses, this way it will be publicly accessible to anyone that can communicate with the machine. This is how you would normally run it in production, for example, in a container.
In most cases you would (and should) have a "termination proxy" handling HTTPS for you on top, this will depend on how you deploy your application, your provider might do this for you, or you might need to set it up yourself.
Tip
You can learn more about it in the [deployment documentation](https://fastapi.tiangolo.com/deployment/).
  *[ CLI]: command line interface
