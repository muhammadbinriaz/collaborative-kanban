from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqError(RuntimeError):
    pass


def groq_configured() -> bool:
    return bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())


async def chat_json(
    *,
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    if not groq_configured():
        raise GroqError("GROQ_API_KEY is not configured")

    payload = {
        "model": settings.GROQ_MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(GROQ_URL, headers=headers, json=payload)
        if response.status_code >= 400:
            logger.error("Groq error %s: %s", response.status_code, response.text[:500])
            raise GroqError(f"Groq request failed ({response.status_code})")
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise GroqError("Groq returned invalid JSON") from exc


async def chat_text(*, system: str, user: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
    if not groq_configured():
        raise GroqError("GROQ_API_KEY is not configured")

    payload = {
        "model": settings.GROQ_MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(GROQ_URL, headers=headers, json=payload)
        if response.status_code >= 400:
            raise GroqError(f"Groq request failed ({response.status_code})")
        data = response.json()
    return data["choices"][0]["message"]["content"].strip()
