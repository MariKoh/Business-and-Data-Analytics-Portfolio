"""Message handler — the per-user decision layer above RAG.

Order of checks for each inbound message:
  1. If user is in handoff AND types a resume trigger → end handoff, greet, resume.
  2. If user is in handoff → return None (bot stays SILENT; a human is handling).
  3. If the message is a handoff trigger → start handoff, send the handoff reply.
  4. Otherwise → answer via the RAG chain.

Centralised here so the LINE webhook and the local simulator share identical
behaviour and it's all unit-testable without LINE or network.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import handoff, products, prompts, smalltalk
from .config import get_settings
from .rag_chain import answer_question

_SMALLTALK_REPLY = {
    "greeting": prompts.GREETING_REPLY,
    "thanks": prompts.THANKS_REPLY,
    "menu": prompts.MENU_REPLY,
}


@dataclass
class HandleResult:
    reply: str | None          # None => send nothing (human is handling)
    kind: str                  # answer | escalated | handoff_started | silent_human | resumed | greeting | thanks | menu
    show_products: bool = False  # attach the product carousel alongside the reply


def handle_message(user_id: str, text: str) -> HandleResult:
    s = get_settings()

    # 1. resume early while in handoff
    if handoff.is_handed_off(user_id) and handoff.is_resume_trigger(text):
        handoff.end_handoff(user_id)
        reply = prompts.RESUME_REPLY if s.handoff_notify_on_resume else None
        return HandleResult(reply=reply, kind="resumed")

    # 2. still inside the human window → stay silent
    if handoff.is_handed_off(user_id):
        return HandleResult(reply=None, kind="silent_human")

    # 3. user asks for a human
    if handoff.is_handoff_trigger(text):
        handoff.start_handoff(user_id)
        return HandleResult(
            reply=prompts.HANDOFF_REPLY.format(hours=int(s.handoff_hours)),
            kind="handoff_started",
        )

    # 4. greetings / thanks / "what can you do" → fast fixed reply, no LLM call
    intent = smalltalk.detect(text)
    if intent:
        return HandleResult(reply=_SMALLTALK_REPLY[intent], kind=intent)

    # 5. normal RAG turn (attach product carousel when it's a product/browse query)
    res = answer_question(text)
    return HandleResult(
        reply=res.answer,
        kind="answer" if res.grounded else "escalated",
        show_products=res.grounded and products.is_product_query(text),
    )
