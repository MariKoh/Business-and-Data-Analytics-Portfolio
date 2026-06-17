"""Human-handoff session state + intent matching.

Behaviour:
  * User types a handoff trigger ("talk to human" / "คุยกับแอดมิน") → the bot goes
    silent for that user for HANDOFF_HOURS so a human admin can take over in LINE.
  * After the window expires, the bot re-enables automatically (lazy: checked on the
    next inbound message).
  * The user can pull the bot back early with a resume trigger ("คุยกับบอท").

Storage: in-memory dict — perfect for local/demo and a single instance. For a
stateless / multi-instance deployment (e.g. Cloud Run scaling to zero), swap the
store for Redis or Firestore. Only this file changes — see docs/HANDOFF.md.

Functions take an optional `now` (epoch seconds) so time logic is unit-testable.
"""
from __future__ import annotations

import time

from .config import get_settings

# user_id -> handoff expiry (epoch seconds)
_handoff_until: dict[str, float] = {}


def start_handoff(user_id: str, hours: float | None = None, now: float | None = None) -> float:
    s = get_settings()
    now = time.time() if now is None else now
    hours = s.handoff_hours if hours is None else hours
    expiry = now + hours * 3600
    _handoff_until[user_id] = expiry
    return expiry


def is_handed_off(user_id: str, now: float | None = None) -> bool:
    """True while the user is in human-handoff mode. Auto-clears when expired."""
    now = time.time() if now is None else now
    expiry = _handoff_until.get(user_id)
    if expiry is None:
        return False
    if now >= expiry:
        _handoff_until.pop(user_id, None)  # window over → bot re-enabled
        return False
    return True


def end_handoff(user_id: str) -> None:
    _handoff_until.pop(user_id, None)


def remaining_seconds(user_id: str, now: float | None = None) -> float:
    now = time.time() if now is None else now
    expiry = _handoff_until.get(user_id)
    return max(0.0, expiry - now) if expiry else 0.0


# --- intent matching --------------------------------------------------------

def _matches(text: str, triggers: list[str]) -> bool:
    t = (text or "").strip().lower()
    return any(trig in t for trig in triggers)


def is_handoff_trigger(text: str) -> bool:
    return _matches(text, get_settings().handoff_trigger_list)


def is_resume_trigger(text: str) -> bool:
    return _matches(text, get_settings().resume_trigger_list)
