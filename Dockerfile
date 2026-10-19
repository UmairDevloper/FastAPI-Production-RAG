FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Point NeMo at the LiteLLM container instead of localhost (local file stays unchanged)
RUN sed -i 's#http://localhost:4000#http://litellm:4000#g' app/security/nemo_guardrails/config.yaml
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]