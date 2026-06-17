"""RAG-chain tests, including the critical anti-hallucination guardrail."""
from unittest.mock import patch

from src.rag_chain import answer_question
from src.retriever import Hit


def test_no_context_triggers_safe_fallback():
    """When retrieval returns nothing, we must NOT call the LLM and must escalate.

    This is the single most important behaviour for a customer-facing bot: no
    context -> no made-up product claims.
    """
    with patch("src.rag_chain.retrieve", return_value=[]), patch(
        "src.rag_chain.chat"
    ) as mock_chat:
        result = answer_question("คำถามที่ไม่มีข้อมูลในฐานความรู้")
        assert result.grounded is False
        assert result.sources == []
        mock_chat.assert_not_called()


def test_grounded_answer_includes_sources():
    fake_hits = [
        Hit(
            text="Calm Down กลิ่นลาเวนเดอร์ ช่วยผ่อนคลายก่อนนอน",
            metadata={"source": "products.md", "section": "Calm Down"},
            score=0.9,
        )
    ]
    with patch("src.rag_chain.retrieve", return_value=fake_hits), patch(
        "src.rag_chain.chat", return_value="แนะนำ Calm Down ค่ะ"
    ):
        result = answer_question("กลิ่นไหนช่วยให้นอนหลับ")
        assert result.grounded is True
        assert "products.md" in result.sources
        assert "Calm Down" in result.answer
