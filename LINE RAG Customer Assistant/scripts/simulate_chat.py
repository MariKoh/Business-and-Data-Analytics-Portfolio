"""Local simulator — run the full per-user flow (handoff + RAG) from the terminal.

Demos and evaluates the assistant WITHOUT a live LINE channel, including the
human-handoff behaviour, so the portfolio piece is verifiable before credentials
and hosting are wired up.

Usage:
    python -m scripts.simulate_chat                 # interactive
    python -m scripts.simulate_chat "กลิ่นไหนช่วยให้นอนหลับ"   # one-shot

Try in interactive mode:
    > คุยกับแอดมิน        (hands off — bot goes silent)
    > ราคาเท่าไหร่         (bot stays silent — a human would reply)
    > คุยกับบอท           (resumes the bot early)
"""
from __future__ import annotations

import sys

sys.path.insert(0, ".")

from src.handler import handle_message  # noqa: E402

USER_ID = "local-user"  # one simulated LINE user for the whole session


def _send(text: str) -> None:
    res = handle_message(USER_ID, text)
    print(f"\n🧑 ลูกค้า: {text}")
    if res.reply is None:
        print("   [🔕 น้องหอม is silent — a human admin would reply here]\n")
    else:
        print(f"🤖 น้องหอม: {res.reply}")
        extra = "  + 🛍️ product carousel (3 items)" if res.show_products else ""
        print(f"   [{res.kind}]{extra}\n")


def main() -> None:
    if len(sys.argv) > 1:
        _send(" ".join(sys.argv[1:]))
        return

    print("MooM HoM assistant — local simulator (Ctrl+C to exit)")
    print("tip: type 'คุยกับแอดมิน' to hand off, 'คุยกับบอท' to resume")
    try:
        while True:
            q = input("\nพิมพ์คำถาม > ").strip()
            if q:
                _send(q)
    except (KeyboardInterrupt, EOFError):
        print("\nbye 👋")


if __name__ == "__main__":
    main()
