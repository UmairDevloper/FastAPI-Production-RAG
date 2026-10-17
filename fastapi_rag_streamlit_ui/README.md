# FastAPI RAG Streamlit UI

A Streamlit frontend for the existing FastAPI documentation RAG API.

## What it currently supports

- Sends questions to `POST /ask`
- Shows the returned answer and insufficient-evidence flag
- Displays source URL, page title, heading path, and evidence ID
- Shows backend latency metrics and UI-measured round-trip time
- Provides request/response JSON inspection
- Includes an API health check and sample questions
- FastAPI-inspired teal/green theme

## Important: streaming

The provided API's `/ask` route returns a completed `AskResponse`. This UI therefore shows a spinner while the request runs; it does not pretend that the answer is token-streamed.

For real token streaming, add a separate backend streaming endpoint that yields incremental text from the generation layer. The current response schema does not expose retrieved evidence text, so source cards can verify citation metadata and open the cited URL, but cannot display the exact retrieved chunk text until the backend includes that evidence in a safe response field.

## Run

From the project root, with the FastAPI API already running:

```powershell
uv add streamlit httpx
$env:RAG_API_BASE_URL = "http://127.0.0.1:8000"
uv run streamlit run streamlit_app.py
```

Alternatively, install the dependencies from this folder:

```powershell
pip install -r requirements.txt
streamlit run streamlit_app.py
```

If the API runs elsewhere, set `RAG_API_BASE_URL` to its base URL. Do not put API secrets in frontend source code.
