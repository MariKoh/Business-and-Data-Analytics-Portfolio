"""Tests for greeting / small-talk detection and handler routing."""
from unittest.mock import patch

from src import handoff, smalltalk
from src.handler import handle_message


def setup_function():
    handoff._handoff_until.clear()


def test_detection():
    assert smalltalk.detect("สวัสดีค่ะ") == "greeting"
    assert smalltalk.detect("Good Morning") == "greeting"
    assert smalltalk.detect("hello") == "greeting"
    assert smalltalk.detect("ขอบคุณมากค่ะ") == "thanks"
    assert smalltalk.detect("thanks!") == "thanks"
    assert smalltalk.detect("ทำอะไรได้บ้าง") == "menu"
    assert smalltalk.detect("what can you do") == "menu"


def test_product_question_is_not_smalltalk():
    # must NOT misfire on real questions
    assert smalltalk.detect("กลิ่นไหนช่วยให้นอนหลับ") is None
    assert smalltalk.detect("ราคาเซ็ต 3 กลิ่นเท่าไหร่") is None
    assert smalltalk.detect("this product is great, ราคาเท่าไหร่") is None  # 'hi' not matched in 'this'


def test_handler_greeting_skips_llm():
    with patch("src.handler.answer_question") as mock_rag:
        r = handle_message("u1", "สวัสดีครับ")
        assert r.kind == "greeting"
        assert "MooM HoM" in r.reply
        mock_rag.assert_not_called()  # no LLM/retrieval cost for greetings


def test_handler_still_answers_product_questions():
    from src.rag_chain import RAGResult

    with patch(
        "src.handler.answer_question",
        return_value=RAGResult(answer="แนะนำ Calm Down ค่ะ", sources=["products.md"], grounded=True),
    ):
        r = handle_message("u2", "กลิ่นไหนช่วยให้นอนหลับ")
        assert r.kind == "answer"
        assert "Calm Down" in r.reply
