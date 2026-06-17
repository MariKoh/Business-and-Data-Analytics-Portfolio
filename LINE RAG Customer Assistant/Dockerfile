# Slim image for the LINE webhook service.
# Note: the embedding model downloads on first run; for faster cold starts you
# can pre-bake it with a `RUN python -c "from sentence_transformers import ..."`.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.hf_cache

WORKDIR /app

# System deps occasionally needed by sentence-transformers / torch wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/knowledge_base/ ./data/knowledge_base/

EXPOSE 8000

# Ingestion (python -m src.ingest) runs separately — it needs Pinecone +
# embedding model and writes to the managed index, not the image.
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
