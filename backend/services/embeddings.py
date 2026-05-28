"""LexaTrace — Sentence-BERT Embedding Service

Generates semantic embeddings using all-MiniLM-L6-v2.
The model is loaded lazily on first use (~80MB download).
"""

import numpy as np
from backend.config import EMBEDDING_MODEL

_model = None


def get_model():
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[LexaTrace] Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("[LexaTrace] Model loaded successfully.")
    return _model


def embed_text(text: str) -> np.ndarray:
    """Embed a single text string into a vector."""
    model = get_model()
    return model.encode(text, normalize_embeddings=True)


def embed_chunks(chunks: list[str]) -> np.ndarray:
    """Embed a list of text chunks into a matrix of vectors.

    Returns:
        np.ndarray of shape (n_chunks, embedding_dim)
    """
    if not chunks:
        return np.array([])
    model = get_model()
    return model.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
