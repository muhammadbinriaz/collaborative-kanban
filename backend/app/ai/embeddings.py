from __future__ import annotations

import hashlib
import logging
import math
from typing import Sequence

import httpx
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

EMBED_DIM = 384


def _hash_embed(text: str, dim: int = EMBED_DIM) -> list[float]:
    """Deterministic bag-of-tokens embedding fallback (no external API)."""
    vec = np.zeros(dim, dtype=np.float32)
    tokens = [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if t]
    if not tokens:
        return vec.tolist()
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec /= norm
    return vec.tolist()


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Prefer HuggingFace Inference API when token is set; otherwise hash embeddings."""
    cleaned = [t.strip() or " " for t in texts]
    if settings.HF_API_TOKEN:
        try:
            return await _hf_embed(cleaned)
        except Exception:
            logger.exception("HF embedding failed; falling back to local hash embeddings")
    return [_hash_embed(text) for text in cleaned]


async def _hf_embed(texts: list[str]) -> list[list[float]]:
    url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.EMBEDDING_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HF_API_TOKEN}"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
        response.raise_for_status()
        data = response.json()

    vectors: list[list[float]] = []
    for item in data:
        arr = np.array(item, dtype=np.float32)
        if arr.ndim == 2:
            arr = arr.mean(axis=0)
        norm = float(np.linalg.norm(arr))
        if norm > 0:
            arr = arr / norm
        # Pad/truncate to EMBED_DIM for pgvector consistency
        flat = arr.flatten()
        if flat.shape[0] < EMBED_DIM:
            flat = np.pad(flat, (0, EMBED_DIM - flat.shape[0]))
        elif flat.shape[0] > EMBED_DIM:
            flat = flat[:EMBED_DIM]
        vectors.append(flat.tolist())
    return vectors


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
