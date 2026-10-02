# Editor Support - FastAPI

Source: https://fastapi.tiangolo.com/editor-support/

# Editor Support[¶](https://fastapi.tiangolo.com/editor-support/#editor-support "Permanent link")
The official [FastAPI Extension](https://marketplace.visualstudio.com/items?itemName=FastAPILabs.fastapi-vscode) enhances your FastAPI development workflow with _path operation_ discovery, navigation, as well as FastAPI Cloud deployment, and live log streaming.
For more details about the extension, refer to the README on the [GitHub repository](https://github.com/fastapi/fastapi-vscode).
## Setup and Installation[¶](https://fastapi.tiangolo.com/editor-support/#setup-and-installation "Permanent link")
The **FastAPI Extension** is available for both [VS Code](https://code.visualstudio.com/) and [Cursor](https://www.cursor.com/). It can be installed directly from the Extensions panel in each editor by searching for "FastAPI" and selecting the extension published by **FastAPI Labs**. The extension also works in browser-based editors such as [vscode.dev](https://vscode.dev) and [github.dev](https://github.dev).
### Application Discovery[¶](https://fastapi.tiangolo.com/editor-support/#application-discovery "Permanent link")
By default, the extension will automatically discover FastAPI applications in your workspace by scanning for files that instantiate `FastAPI()`. If auto-detection doesn't work for your project structure, you can specify an entrypoint via `[tool.fastapi]` in `pyproject.toml` or the `fastapi.entryPoint` VS Code setting using module notation (e.g. `myapp.main:app`).
## Features[¶](https://fastapi.tiangolo.com/editor-support/#features "Permanent link")
  * **Path Operation Explorer** - A sidebar tree view of all _path operations_ in your application. Click to jump to any route or router definition.
  * **Route Search** - Search by path, method, or name with `Ctrl` + `Shift` + `E` (on macOS: `Cmd` + `Shift` + `E`).
  * **CodeLens Navigation** - Clickable links above test client calls (e.g. `client.get('/items')`) that jump to the matching _path operation_ for quick navigation between tests and implementation.
  * **Deploy to FastAPI Cloud** - One-click deployment of your app to [FastAPI Cloud](https://fastapicloud.com/).
  * **Stream Application Logs** - Real-time log streaming from your FastAPI Cloud-deployed application with level filtering and text search.


If you'd like to familiarize yourself with the extension's features, you can check out the extension walkthrough by opening the Command Palette (`Ctrl` + `Shift` + `P` or on macOS: `Cmd` + `Shift` + `P`) and selecting "Welcome: Open walkthrough..." and then choosing the "Get started with FastAPI" walkthrough.
