"""Tests for product-intent detection and the carousel trigger in the handler."""
from unittest.mock import patch

from src import handoff, products
from src.handler import handle_message
from src.rag_chain import RAGResult


def setup_function():
    handoff._handoff_until.clear()


def test_product_intent_detection():
    assert products.is_product_query("มีกลิ่นอะไรบ้าง") is True
    assert products.is_product_query("ราคาเท่าไหร่") is True
    assert products.is_product_query("ขอข้อมูล Calm Down") is True
    assert products.is_product_query("ดูสินค้าหน่อย") is True
    # not a product/browse query
    assert products.is_product_query("วิธีใช้ก้านไม้หอมยังไง") is True  # 'ก้านไม้หอม' is a product kw
    assert products.is_product_query("สวัสดีครับ") is False
    assert products.is_product_query("คุยกับแอดมิน") is False


def test_carousel_attached_on_product_query():
    with patch(
        "src.handler.answer_question",
        return_value=RAGResult(answer="เรามี 3 กลิ่นค่ะ", sources=["products.md"], grounded=True),
    ):
        r = handle_message("u1", "มีกลิ่นอะไรบ้าง ราคาเท่าไหร่")
        assert r.kind == "answer"
        assert r.show_products is True


def test_no_carousel_on_non_product_query():
    with patch(
        "src.handler.answer_question",
        return_value=RAGResult(answer="ส่งฟรีเมื่อครบ 590 บาทค่ะ", sources=["faq.md"], grounded=True),
    ):
        r = handle_message("u2", "ส่งฟรีไหม")
        assert r.show_products is False


def test_no_carousel_when_not_grounded():
    with patch(
        "src.handler.answer_question",
        return_value=RAGResult(answer="...", sources=[], grounded=False),
    ):
        # even if it mentions a product word, don't attach a carousel to a non-answer
        r = handle_message("u3", "มีสาขาขายสินค้าที่เชียงใหม่ไหม")
        assert r.show_products is False
