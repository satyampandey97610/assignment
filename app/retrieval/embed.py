"""Wrapper for local multilingual sentence embeddings using sentence-transformers."""

from collections.abc import Sequence

from sentence_transformers import SentenceTransformer

from app.config import settings

_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    """Return a singleton instance of the SentenceTransformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBED_MODEL)
    return _model


def embed_query(query: str) -> list[float]:
    """Generate dense embedding for a query with required 'query: ' prefix."""
    model = get_embedder()
    text = f"query: {query.strip()}"
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_passages(passages: Sequence[str]) -> list[list[float]]:
    """Generate dense embeddings for passages with required 'passage: ' prefix."""
    model = get_embedder()
    texts = [f"passage: {p.strip()}" for p in passages]
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()
