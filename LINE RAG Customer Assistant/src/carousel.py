"""Builds the LINE product carousel (a Template carousel message).

Kept in the transport layer (LINE-specific) so the handler stays channel-agnostic.
Uses CarouselTemplate for reliability; each card shows image, name+scent, price,
and two actions: buy on Shopee, or ask in this chat.
"""
from __future__ import annotations

from linebot.v3.messaging import (
    CarouselColumn,
    CarouselTemplate,
    MessageAction,
    TemplateMessage,
    URIAction,
)

from .products import LINE_OA_URL, PRODUCTS, SHOPEE_STORE_URL


def build_product_carousel() -> TemplateMessage:
    columns = []
    for p in PRODUCTS:
        # title <=40 chars, text <=60 chars (LINE limits)
        title = f"{p.name_en} ({p.scent_th})"[:40]
        text = f"{p.blurb_th} • {p.price_thb} บาท"[:60]
        columns.append(
            CarouselColumn(
                thumbnail_image_url=p.image_url,
                title=title,
                text=text,
                actions=[
                    URIAction(label="สั่งซื้อบน Shopee", uri=SHOPEE_STORE_URL),
                    MessageAction(label="สอบถามกลิ่นนี้", text=f"ขอข้อมูล {p.name_en}"),
                ],
            )
        )

    return TemplateMessage(
        alt_text="สินค้า MooM HoM — ก้านไม้หอม 3 กลิ่น",
        template=CarouselTemplate(columns=columns),
    )
