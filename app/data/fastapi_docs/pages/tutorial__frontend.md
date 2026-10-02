# Frontend - FastAPI

Source: https://fastapi.tiangolo.com/tutorial/frontend/

# Frontend[¶](https://fastapi.tiangolo.com/tutorial/frontend/#frontend "Permanent link")
You can serve static frontend apps with `app.frontend()` (or `router.frontend()`).
This is useful for frontend tools that generate static files, like React with Vite, TanStack Router, Astro, Vue, Svelte, Angular, Solid, and others.
With these tools, you normally have a step that builds the frontend, with a command like:

```
npm run build

```

That would generate a directory like `./dist/` with your frontend files.
You can use `app.frontend()` to serve that directory following the conventions needed by these frontend frameworks.
**FastAPI** checks _path operations_ first. The frontend files are checked only if no normal route matched, so your API won't be affected.
## Serve a Frontend[¶](https://fastapi.tiangolo.com/tutorial/frontend/#serve-a-frontend "Permanent link")
After building your frontend, for example with `npm run build`, put the generated files in a directory, for example, `dist`.
Your project structure could look like this:

```
.
├── pyproject.toml
├── app
│   ├── __init__.py
│   └── main.py
└── dist
    ├── index.html
    └── assets
        └── app.js

```

Then serve it with `app.frontend()`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/frontend/#__tabbed_1_1)

```
from fastapi import FastAPI

app = FastAPI()

app.frontend("/", directory="dist")

```

With this, a request for `/assets/app.js` can serve `dist/assets/app.js`.
If you also have a **FastAPI** _path operation_ , the _path operation_ wins.
## Client-Side Routing[¶](https://fastapi.tiangolo.com/tutorial/frontend/#client-side-routing "Permanent link")
Many frontend apps, including **single-page apps** (SPAs), use client-side routing. A path like `/dashboard/settings` might not be a real file but the framework would take care of handling it.
So, if accessing that URL directly (instead of navigating through the app), the backend should serve the frontend app from `index.html`, so that the frontend framework can then handle the client-side routing.
For that, use `fallback="index.html"`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/frontend/#__tabbed_2_1)

```
from fastapi import FastAPI

app = FastAPI()

app.frontend("/", directory="dist", fallback="index.html")

```

**FastAPI** uses this fallback only for `GET` and `HEAD` requests that explicitly accept HTML with `Accept: text/html` or `Accept: application/xhtml+xml`, as browser navigation requests normally do. Missing files like JavaScript, CSS, and images still return `404`.
Requests with other methods, like `POST` or `PUT`, to paths that only match the frontend fallback also return `404`. Regular **FastAPI** _path operations_ still have higher priority than frontend routes.
Tip
By default, `fallback` has a value of `fallback="auto"`. In most cases you won't need to specify `fallback`. Read below for details.
This is what you would want with many frontend apps that use client-side routing, for example, React with TanStack Router, Vue, Angular, SvelteKit, or Solid.
## Custom 404 Page[¶](https://fastapi.tiangolo.com/tutorial/frontend/#custom-404-page "Permanent link")
You can also serve a static `404.html` page for missing frontend paths:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/frontend/#__tabbed_3_1)

```
from fastapi import FastAPI

app = FastAPI()

app.frontend("/", directory="dist", fallback="404.html")

```

That response keeps a status code of `404`.
In this case, **FastAPI** won't serve `index.html` for missing frontend paths. It will return the `404.html` file instead.
Tip
By default, `fallback` has a value of `fallback="auto"`. With this, if a `404.html` file is found, it will be used as the fallback automatically.
So, you can normally omit the `fallback` argument.
This is useful with frontend tools that generate static HTML files for each page, like Astro.
## Fallback Auto[¶](https://fastapi.tiangolo.com/tutorial/frontend/#fallback-auto "Permanent link")
By default, `app.frontend()` uses `fallback="auto"`.
If there is a `404.html` file in the frontend directory, missing frontend paths serve that file with status code `404`.
Otherwise, if there is an `index.html` file, missing browser navigation paths serve `index.html`, which is what many frontend apps with client-side routing expect.
So, in most cases you can use `app.frontend("/", directory="dist")` without specifying the `fallback` argument.
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/frontend/#__tabbed_4_1)

```
from fastapi import FastAPI

app = FastAPI()

app.frontend("/", directory="dist")

```

## Disable Fallback[¶](https://fastapi.tiangolo.com/tutorial/frontend/#disable-fallback "Permanent link")
If you don't want to serve a fallback file for missing frontend paths, use `fallback=None`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/frontend/#__tabbed_5_1)

```
from fastapi import FastAPI

app = FastAPI()

app.frontend("/", directory="dist", fallback=None)

```

Then missing frontend paths return the normal `404`.
## Check Directory[¶](https://fastapi.tiangolo.com/tutorial/frontend/#check-directory "Permanent link")
By default, `app.frontend()` uses `check_dir="auto"`.
When the `FASTAPI_ENV` environment variable is set to `development`, **FastAPI** only shows a warning if the frontend build output directory is missing. The [`fastapi dev` command](https://github.com/fastapi/fastapi-cli#fastapi-dev) sets this environment variable for you if it is not already set. This lets you start the backend before building or starting the frontend during development.
In any other environment, **FastAPI** raises an error when the app is created. This helps catch configuration errors early before deploying an app without its frontend files.
You can also set `check_dir=True` to always check the directory when the app is created.
If your frontend files are created later, for example by a separate build step after the app object is created, set `check_dir=False`:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/frontend/#__tabbed_6_1)

```
from fastapi import FastAPI

app = FastAPI()

app.frontend("/", directory="dist", check_dir=False)

```

With `check_dir=False`, **FastAPI** will not check the directory when the app is created. If the configured directory is still missing when a request is handled, **FastAPI** will raise an error then.
## Use it with `APIRouter`[¶](https://fastapi.tiangolo.com/tutorial/frontend/#use-it-with-apirouter "Permanent link")
You can also add frontend files to an `APIRouter` and include it with a prefix:
[Python 3.10+](https://fastapi.tiangolo.com/tutorial/frontend/#__tabbed_7_1)

```
from fastapi import APIRouter, FastAPI

app = FastAPI()
router = APIRouter()

router.frontend("/", directory="dist", fallback="index.html")
app.include_router(router, prefix="/app")

```

In this example, frontend paths are served under `/app`.
Any regular _path operations_ in the app will still take precedence, including in other routers.
## Dependencies and Middleware[¶](https://fastapi.tiangolo.com/tutorial/frontend/#dependencies-and-middleware "Permanent link")
Frontend responses run inside the normal **FastAPI** application, so HTTP middleware applies to them.
Dependencies from the app, from an `APIRouter`, and from `include_router()` also apply to frontend responses. This can be useful for protecting a frontend with cookie authentication or similar.
Dependencies can also modify response headers and add background tasks, as with normal _path operations_.
## Static Build Output Only[¶](https://fastapi.tiangolo.com/tutorial/frontend/#static-build-output-only "Permanent link")
`app.frontend()` serves files already generated by your frontend build.
It does not run server-side rendering. It is for frontend frameworks that generate static files, not for frameworks that need dynamic rendering on the server for each request.
