FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install curl, build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first to avoid downloading huge CUDA wheels
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Copy pyproject.toml and install project dependencies
COPY pyproject.toml .
RUN pip install .[dev]

# Pre-download the sentence-transformers model so container runs offline
ENV HF_HOME=/root/.cache/huggingface
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-small')"

# Copy application code and assets
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && python -m app.retrieval.ingest && uvicorn app.api.main:app --host 0.0.0.0 --port 8000"]
