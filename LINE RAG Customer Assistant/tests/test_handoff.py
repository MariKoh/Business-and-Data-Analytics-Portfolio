"""Tests for the human-handoff feature (pure Python — no external services)."""
from unittest.mock import patch

from src import handoff
from src.handler import handle_message
from src.rag_chain import RAGResult


def setup_function():
    # isolate state between tests
    handoff._handoff_until.clear()


def test_handoff_starts_and_blocks_then_expires():
    now = 1_000_000.0
    handoff.start_handoff("u1", hours=3, now=now)

    # within the 3h window → handed off
    assert handoff.is_handed_off("u1", now=now + 60) is True
    assert handoff.is_handed_off("u1", now=now + 3 * 3600 - 1) is True

    # after the window → auto re-enabled
    assert handoff.is_handed_off("u1", now=now + 3 * 3600 + 1) is False


def test_trigger_detection():
    assert handoff.is_handoff_trigger("ขอคุยกับแอดมินหน่อยค่ะ") is True
    assert handoff.is_handoff_trigger("talk to human please") is True
    assert handoff.is_handoff_trigger("กลิ่นไหนช่วยให้นอนหลับ") is False
    assert handoff.is_resume_trigger("คุยกับบอท") is True


def test_handler_starts_handoff_then_stays_silent():
    # 1. user requests a human → handoff reply, state set
    r1 = handle_message("u2", "ขอคุยกับแอดมิน")
    assert r1.kind == "handoff_started"
    assert r1.reply is not None and "แอดมิน" in r1.reply

    # 2. next message while handed off → bot is SILENT (human handles)
    with patch("src.handler.answer_question") as mock_rag:
        r2 = handle_message("u2", "ราคาเท่าไหร่")
        assert r2.kind == "silent_human"
        assert r2.reply is None
        mock_rag.assert_not_called()


def test_handler_resume_brings_bot_back():
    handle_message("u3", "talk to human")
    r = handle_message("u3", "คุยกับบอท")
    assert r.kind == "resumed"
    assert r.reply is not None

    # after resume, normal RAG runs again
    with patch(
        "src.handler.answer_question",
        return_value=RAGResult(answer="แนะนำ Calm Down ค่ะ", sources=["products.md"], grounded=True),
    ):
        r2 = handle_message("u3", "กลิ่นไหนช่วยให้นอนหลับ")
        assert r2.kind == "answer"
        assert "Calm Down" in r2.reply


def test_handoff_is_per_user():
    handle_message("userA", "talk to human")
    # userB is unaffected
    with patch(
        "src.handler.answer_question",
        return_value=RAGResult(answer="สวัสดีค่ะ", sources=[], grounded=True),
    ):
        rb = handle_message("userB", "สวัสดี")
        assert rb.kind == "answer"
