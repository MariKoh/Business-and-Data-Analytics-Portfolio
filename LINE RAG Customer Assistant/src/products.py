"""Product catalog data + product-intent detection (for the LINE carousel).

To use real assets later, edit only this file: SHOPEE_STORE_URL, LINE_OA_URL,
and each Product's image_url (public HTTPS, ~1024x678, PNG/JPEG).

The carousel is shown when a customer's message looks like a product/browse/price
query. Images are placeholders for now — replace `image_url` with real HTTPS URLs
(Shopee/IG product photos) and the store/LINE links below when ready.
"""
from __future__ import annotations

from dataclasses import dataclass

# --- EDIT THESE when you have real assets/links ---------------------------
SHOPEE_STORE_URL = "https://shopee.co.th/moomhom"        # TODO: real Shopee store URL
LINE_OA_URL = "https://line.me/R/ti/p/@moomhom"          # TODO: real @id / lin.ee link
# Placeholder images (on-brand charcoal/ivory). Swap for real product photos.
_IMG = "https://placehold.co/1024x678/2C2C2C/FAF8F5/png?text="


@dataclass
class Product:
    id: str
    name_en: str
    scent_th: str
    price_thb: int
    blurb_th: str
    image_url: str


PRODUCTS: list[Product] = [
    Product("calm_down", "Calm Down", "ลาเวนเดอร์", 390,
            "ผ่อนคลายก่อนนอน หลับสบาย", _IMG + "Calm+Down"),
    Product("main_character", "Main Character", "เบอร์กามอต-ส้ม", 390,
            "สดชื่น มีพลัง เหมาะกับโต๊ะทำงาน", _IMG + "Main+Character"),
    Product("soft_drama", "Soft Drama", "มะลิ", 390,
            "หรูละมุน อบอวลมีระดับ", _IMG + "Soft+Drama"),
]


# Keywords that should surface the product carousel (substring, case-insensitive).
_PRODUCT_KEYWORDS = (
    # browse / catalog
    "สินค้า", "ดูสินค้า", "มีกลิ่นอะไร", "กลิ่นอะไรบ้าง", "มีกลิ่นไหน", "มีรุ่นไหน",
    "ทั้งหมด", "แค็ตตาล็อก", "แคตตาล็อก", "catalog", "products",
    # price / promo
    "ราคา", "กี่บาท", "เซ็ต", "โปรโม", "โปรโมชัน", "price",
    # recommend
    "แนะนำกลิ่น", "แนะนำสินค้า",
    # product names / scents
    "calm down", "main character", "soft drama", "ลาเวนเดอร์", "มะลิ", "เบอร์กามอต",
    "ก้านไม้หอม", "diffuser", "reed",
)


def is_product_query(text: str) -> bool:
    t = (text or "").strip().lower()
    return any(kw in t for kw in _PRODUCT_KEYWORDS)
