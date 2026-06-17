"""LLM client wrapper for OpenRouter (course EP.9).

OpenRouter is OpenAI-compatible, so we use the OpenAI SDK pointed at OpenRouter's
base URL. Wrapping it here keeps model/provider choice and retry policy in one
place; the rag_chain stays provider-agnostic.
"""
from __future__ import annotations

from openai import OpenAI

from .config import get_settings


def get_client() -> OpenAI:
    s = get_settings()
    return OpenAI(api_key=s.openrouter_api_key, base_url=s.openrouter_base_url)


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    s = get_settings()
    client = get_client()
    resp = client.chat.completions.create(
        model=s.llm_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # Optional OpenRouter attribution headers (safe to omit)
        extra_headers={"X-Title": "MooM HoM LINE RAG Assistant"},
    )
    return resp.choices[0].message.content.strip()
