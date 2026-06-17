"""RAG orchestration: retrieve -> ground -> generate, with citations.

Single entry point used by both the LINE webhook and the local simulator, so
behaviour is identical in demo and production.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from loguru import logger

from . import prompts
from .llm import chat
from .retriever import format_context, retrieve


@dataclass
class RAGResult:
    answer: str
    sources: list[str] = field(default_factory=list)
    grounded: bool = True


def answer_question(question: str) -> RAGResult:
    """Run one RAG turn. Falls back to a safe reply when nothing is retrieved."""
    hits = retrieve(question)

    if not hits:
        logger.warning("No context retrieved for: {!r}", question)
        return RAGResult(answer=prompts.NO_CONTEXT_REPLY, sources=[], grounded=False)

    context = format_context(hits)
    user_prompt = prompts.ANSWER_PROMPT.format(context=context, question=question)
    answer = chat(prompts.SYSTEM_PROMPT, user_prompt)

    sources = sorted({h.metadata.get("source", "kb") for h in hits})
    return RAGResult(answer=answer, sources=sources, grounded=True)
