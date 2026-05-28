"""LexaTrace — Cosine Similarity Engine

Compares input embeddings against a reference corpus using cosine similarity.
Includes a built-in reference corpus of sample copyrighted content for demo purposes.
"""

import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from backend.config import THRESHOLD_HIGH, THRESHOLD_MEDIUM, THRESHOLD_LOW

# ── Demo reference corpus ──
# In production, this would be loaded from Elasticsearch / a vector DB.
REFERENCE_CORPUS = [
    {
        "id": "ref-001",
        "source": "IEEE Trans. Pattern Analysis, Vol. 42",
        "type": "Academic Paper",
        "section": "Methodology — Section 3.2",
        "jurisdiction": "US",
        "text": "Deep neural networks have revolutionized computer vision by learning hierarchical feature representations directly from raw pixel data. Convolutional neural networks in particular leverage spatial locality through shared weight kernels that slide across the input feature maps, producing translation-equivariant representations."
    },
    {
        "id": "ref-002",
        "source": "arXiv:2304.12749 — Neural Style Transfer Survey",
        "type": "Preprint",
        "section": "Abstract & Introduction",
        "jurisdiction": "Global",
        "text": "Neural style transfer is a technique that applies the artistic style of one image to the content of another image using deep neural networks. The seminal work by Gatys et al demonstrated that convolutional neural networks can separate and recombine image content and style, enabling the creation of artistic images."
    },
    {
        "id": "ref-003",
        "source": "US Patent 10,234,567 — Image Processing Method",
        "type": "Patent",
        "section": "Claim 1, Sub-claims 1a–1c",
        "jurisdiction": "US",
        "text": "A method for processing digital images comprising receiving an input image, applying a series of convolutional filters to extract feature maps at multiple scales, computing attention weights across spatial positions, and generating an output image with enhanced visual properties through learned transformations."
    },
    {
        "id": "ref-004",
        "source": "MIT-Licensed Repository: fast-style-tf",
        "type": "Source Code",
        "section": "utils/transform.py — Lines 45–112",
        "jurisdiction": "Global",
        "text": "def transform_image(content_image, style_image, model, alpha=1.0): content_features = model.encode(content_image) style_features = model.encode(style_image) gram_style = compute_gram_matrix(style_features) output = optimize_image(content_features, gram_style, alpha) return postprocess(output)"
    },
    {
        "id": "ref-005",
        "source": "Springer: Computer Vision & Applications",
        "type": "Textbook",
        "section": "Chapter 8 — Feature Extraction",
        "jurisdiction": "EU",
        "text": "Feature extraction is the process of transforming raw data into a reduced set of features that still contains the most relevant information. In computer vision, features can be edges, corners, textures, or more abstract learned representations from deep neural networks."
    },
    {
        "id": "ref-006",
        "source": "EP Patent 3,456,789 — Natural Language Processing System",
        "type": "Patent",
        "section": "Claims 1–4",
        "jurisdiction": "EU",
        "text": "A system for processing natural language text comprising a tokenizer module that segments input text into subword units, an encoder module with multi-head self-attention layers that processes the tokens into contextual representations, and a classifier head that maps representations to output categories."
    },
    {
        "id": "ref-007",
        "source": "ACM Computing Surveys, Vol. 54, No. 3",
        "type": "Academic Paper",
        "section": "Section 4 — Transformer Architectures",
        "jurisdiction": "US",
        "text": "The transformer architecture introduced by Vaswani et al relies entirely on self-attention mechanisms, dispensing with recurrence and convolutions. The key innovation is the scaled dot-product attention which computes compatibility between queries and keys to produce weighted sums of values."
    },
    {
        "id": "ref-008",
        "source": "GPL-3.0 Repository: opendetect-ml",
        "type": "Source Code",
        "section": "core/detector.py — Lines 1–80",
        "jurisdiction": "Global",
        "text": "class CopyrightDetector: def __init__(self, model_name): self.model = load_pretrained(model_name) self.threshold = 0.85 def detect(self, text): embeddings = self.model.encode(text) similarities = cosine_similarity(embeddings, self.corpus) return self.rank_matches(similarities)"
    },
    {
        "id": "ref-009",
        "source": "WIPO PCT/US2023/012345 — Machine Learning Pipeline",
        "type": "Patent",
        "section": "Description — Preferred Embodiment",
        "jurisdiction": "Global",
        "text": "The machine learning pipeline includes data ingestion from multiple sources, automated feature engineering using genetic programming, model selection through Bayesian optimization, and deployment through containerized microservices with continuous monitoring and retraining capabilities."
    },
    {
        "id": "ref-010",
        "source": "Nature Machine Intelligence, Vol. 5",
        "type": "Academic Paper",
        "section": "Results — Table 2",
        "jurisdiction": "Global",
        "text": "Our experimental results demonstrate that the proposed approach achieves state-of-the-art performance on all benchmark datasets. The model achieves an F1 score of 94.2 on the standard test set, surpassing the previous best result by 2.3 percentage points while using 40% fewer parameters."
    },
]

# Pre-computed embeddings cache
_ref_embeddings = None
_ref_texts = None


def _get_reference_embeddings():
    """Lazily compute embeddings for the reference corpus."""
    global _ref_embeddings, _ref_texts
    if _ref_embeddings is None:
        from backend.services.embeddings import embed_chunks
        _ref_texts = [r["text"] for r in REFERENCE_CORPUS]
        _ref_embeddings = embed_chunks(_ref_texts)
    return _ref_embeddings


def classify_risk(score: float) -> str:
    """Classify a similarity score into risk level."""
    if score >= THRESHOLD_HIGH:
        return "high"
    elif score >= THRESHOLD_MEDIUM:
        return "medium"
    elif score >= THRESHOLD_LOW:
        return "low"
    return "clear"


def find_matches(chunk_embeddings: np.ndarray, chunks: list[str], top_k: int = 10) -> list[dict]:
    """Find the top-K most similar reference items for the given chunks.

    Returns a list of match dicts sorted by score descending.
    """
    ref_embeddings = _get_reference_embeddings()
    if ref_embeddings.size == 0 or chunk_embeddings.size == 0:
        return []

    # Compute similarity matrix: (n_chunks x n_refs)
    sim_matrix = cosine_similarity(chunk_embeddings, ref_embeddings)

    # For each reference, take the max similarity across all input chunks
    best_scores = sim_matrix.max(axis=0)  # shape: (n_refs,)
    best_chunk_idx = sim_matrix.argmax(axis=0)  # which input chunk matched best

    matches = []
    for ref_idx in range(len(REFERENCE_CORPUS)):
        score = float(best_scores[ref_idx])
        if score < 0.3:  # Skip very low matches
            continue
        ref = REFERENCE_CORPUS[ref_idx]
        chunk_idx = int(best_chunk_idx[ref_idx])
        matches.append({
            "ref_id": ref["id"],
            "source": ref["source"],
            "type": ref["type"],
            "section": ref["section"],
            "jurisdiction": ref["jurisdiction"],
            "score": round(score, 4),
            "risk_level": classify_risk(score),
            "matched_chunk": chunks[chunk_idx][:200] + "..." if len(chunks[chunk_idx]) > 200 else chunks[chunk_idx],
            "ref_excerpt": ref["text"][:200] + "..." if len(ref["text"]) > 200 else ref["text"],
        })

    # Sort by score descending, take top_k
    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches[:top_k]


def compute_overall_risk(matches: list[dict]) -> dict:
    """Compute overall risk score and counts from matches."""
    if not matches:
        return {"risk_score": 0.0, "risk_level": "clear", "high": 0, "medium": 0, "low": 0, "total": 0}

    high = sum(1 for m in matches if m["risk_level"] == "high")
    medium = sum(1 for m in matches if m["risk_level"] == "medium")
    low = sum(1 for m in matches if m["risk_level"] == "low")

    # Weighted score: high matches weigh more
    weights = {"high": 1.0, "medium": 0.6, "low": 0.3, "clear": 0.0}
    weighted_sum = sum(m["score"] * weights.get(m["risk_level"], 0) for m in matches)
    max_possible = sum(weights.get(m["risk_level"], 0) for m in matches) or 1
    risk_score = round((weighted_sum / max_possible) * 100, 1)

    if high >= 2:
        level = "high"
    elif high >= 1 or medium >= 3:
        level = "medium"
    elif medium >= 1:
        level = "low"
    else:
        level = "clear"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "high": high,
        "medium": medium,
        "low": low,
        "total": len(matches),
    }
