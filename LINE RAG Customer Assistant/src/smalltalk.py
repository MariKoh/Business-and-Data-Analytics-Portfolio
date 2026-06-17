"""Greeting / small-talk intent detection.

Handles the messages that aren't product questions (hello, thanks, "what can you
do") with fast, fixed replies — no LLM call, no retrieval. This keeps the first
impression warm instead of immediately escalating, and costs nothing.

Detection is intentionally conservative: greetings/thanks are usually short,
standalone messages, so we match distinctive Thai tokens (substring) and
whole-word English greetings to avoid misfiring on real product questions.
"""
from __future__ import annotations

# Distinctive Thai tokens — safe as substrings (won't appear in product questions).
_GREETING_TH = ("สวัสดี", "หวัดดี", "ดีจ้า", "ดีครับ", "ดีค่ะ", "ทักทาย")
_THANKS_TH = ("ขอบคุณ", "ขอบใจ", "ขอบคุน")
_MENU_TH = ("ทำอะไรได้บ้าง", "ตอบอะไรได้บ้าง", "ช่วยอะไรได้บ้าง", "มีอะไรบ้าง", "ทำอะไรได้")

# English greetings — matched as whole words to avoid false hits (e.g. "hi" in "this").
_GREETING_EN = {"hi", "hello", "hey", "hallo", "yo"}
_GREETING_EN_PREFIX = ("good morning", "good afternoon", "good evening", "good day")
_THANKS_EN = {"thanks", "thank", "thx", "ty"}
_MENU_EN = ("what can you do", "what do you do", "how can you help", "what can you help")


def _has_token(text: str, tokens) -> bool:
    return any(tok in text for tok in tokens)


def _has_word(text: str, words: set[str]) -> bool:
    return bool(words.intersection(text.replace("!", " ").replace("?", " ").split()))


def detect(text: str) -> str | None:
    """Return 'greeting' | 'thanks' | 'menu' | None."""
    t = (text or "").strip().lower()
    if not t:
        return None

    # menu / capability first (most specific phrasing)
    if _has_token(t, _MENU_TH) or any(p in t for p in _MENU_EN):
        return "menu"
    if _has_token(t, _THANKS_TH) or _has_word(t, _THANKS_EN):
        return "thanks"
    if (
        _has_token(t, _GREETING_TH)
        or _has_word(t, _GREETING_EN)
        or any(t.startswith(p) for p in _GREETING_EN_PREFIX)
    ):
        return "greeting"
    return None
