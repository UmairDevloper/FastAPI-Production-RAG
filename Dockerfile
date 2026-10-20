FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential git \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface
WORKDIR /home/user/app

# LiteLLM in an isolated environment
RUN python -m venv /home/user/litellm-venv && \
    /home/user/litellm-venv/bin/pip install --no-cache-dir "litellm[proxy]"

# App dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

EXPOSE 7860
CMD ["bash", "-c", "/home/user/litellm-venv/bin/litellm --config app/docker/litellm/litellm_config.prod.yaml --port 4000 & exec uvicorn app.main:app --host 0.0.0.0 --port 7860"]