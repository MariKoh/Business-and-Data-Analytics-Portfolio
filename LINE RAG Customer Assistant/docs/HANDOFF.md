# Human Handoff

Lets a customer reach a real person and pauses the bot so it doesn't talk over the
admin — then brings the bot back automatically.

## Behaviour

1. **Trigger** — the user sends a handoff phrase (e.g. *"คุยกับแอดมิน"*, *"talk to
   human"*). The bot replies once to confirm, then **goes silent for that user**.
2. **Human window** — for `HANDOFF_HOURS` (default **3**), the bot ignores that
   user's messages, so the admin's replies in LINE (via OA Manager Chat) stand alone.
3. **Auto re-enable** — once the window passes, the bot resumes automatically on the
   user's next message. No manual reset needed.
4. **Early resume (optional)** — the user can bring the bot back before the window
   ends by sending a resume phrase (e.g. *"คุยกับบอท"*).

Handoff is **per LINE user** — pausing one customer never affects others.

## Why "go silent" rather than forward?

With the Messaging API webhook enabled, an admin can still message the customer
from the LINE OA Manager **Chat** screen. The only thing needed for a clean human
takeover is for the bot to stop auto-replying — which is exactly what the silent
window does. (Optionally, switch that thread to Manual/Chat mode in OA Manager for
an extra layer.)

## Configuration (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `HANDOFF_HOURS` | `3` | Length of the silent human window |
| `HANDOFF_TRIGGERS` | (Thai+EN list) | Phrases that start a handoff (substring match, case-insensitive) |
| `RESUME_TRIGGERS` | (Thai+EN list) | Phrases that end it early |
| `HANDOFF_NOTIFY_ON_RESUME` | `true` | Whether to send a short "I'm back" message |

## Try it locally

```bash
make chat
> ขอคุยกับแอดมิน        # → confirm + hand off
> ราคาเท่าไหร่           # → [bot silent — a human would reply]
> คุยกับบอท             # → bot resumes
```

## Code map

| Concern | File |
|---|---|
| Session state + expiry + trigger matching | `src/handoff.py` |
| Decision flow (resume / silent / handoff / RAG) | `src/handler.py` |
| Confirmation & resume messages (น้องหอม voice) | `src/prompts.py` |
| Wiring into LINE | `src/app.py` |
| Tests | `tests/test_handoff.py` |

## Production note — state persistence

The default store is an **in-memory dict** in `src/handoff.py`. That's correct for
local/demo and a single always-on instance, but it has two limits in production:

- **Restart** clears active handoffs.
- **Multiple instances** (e.g. Cloud Run scaling out, or scale-to-zero) don't share
  the dict, so a user could hit an instance that doesn't know they're handed off.

For production, swap the in-memory dict for a shared store with TTL — **Redis**
(Upstash has a free tier) is the natural fit because handoffs are just keys with an
expiry:

```python
# sketch — replace the dict in handoff.py
# start:  redis.setex(f"handoff:{user_id}", int(hours*3600), "1")
# check:  bool(redis.exists(f"handoff:{user_id}"))   # TTL handles expiry for free
# end:    redis.delete(f"handoff:{user_id}")
```

Only `src/handoff.py` changes — the handler, app, and tests stay the same.
