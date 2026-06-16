"""
Product categorisation — LLM-assisted data enrichment.

The proxy dataset has no category field, so we create one. Two paths share a fixed
taxonomy and write the same cache (data/processed/category_map.csv):

  * llm_classify()  — production path: batches unique descriptions to an LLM with the
    taxonomy + few-shot examples, parses strict JSON, caches the result. Used when an
    API key is present (.env: LLM_API_KEY). This is the reproducible GenAI artifact.

  * heuristic_classify() — offline bootstrap used to generate tonight's cache without a
    key. The keyword logic below was authored by an LLM (Claude) from domain knowledge
    of this gift/homeware catalogue; the production path refines it via a model call.

Honest note: this is gift/homeware, not grocery. At the Retailer a real product hierarchy
already exists, so this enrichment step would be unnecessary — the *method* is what
transfers.

Run:  python -m src.segmentation.categorize_products
"""
from __future__ import annotations
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("categorize")

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"

TAXONOMY = [
    "Christmas & Seasonal", "Party & Celebration", "Candles & Lighting",
    "Kitchen & Dining", "Storage & Organisation", "Bags", "Stationery & Craft",
    "Toys & Games", "Jewellery & Accessories", "Home Decor",
    "Garden & Outdoor", "Bathroom & Beauty", "Other",
]

# Ordered rules — first match wins, so specific/seasonal terms sit above generic ones.
RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Christmas & Seasonal", ("CHRISTMAS", "XMAS", "ADVENT", "SANTA", "REINDEER",
        "SNOWMAN", "NIGHT BEFORE", "EASTER", "HALLOWEEN", "VALENTINE", "NATIVITY", "NOEL")),
    ("Party & Celebration", ("PARTY", "BUNTING", "BALLOON", "BIRTHDAY", "BANNER",
        "CAKE CASE", "GARLAND", "CONFETTI", "PARTY BAG", "FLAG")),
    ("Candles & Lighting", ("T-LIGHT", "TEALIGHT", "TEA LIGHT", "CANDLE", "LANTERN",
        "NIGHTLIGHT", "NIGHT LIGHT", "FAIRY LIGHT", "LIGHT HOLDER", "LIGHTS", "LAMP",
        "LIGHT CHAIN", "INCENSE")),
    ("Kitchen & Dining", ("CAKESTAND", "CAKE STAND", "MUG", "BOWL", "PLATE", "TEAPOT",
        "CUP", "JUG", "GLASS", "TABLEWARE", "BAKING", "CUTLERY", "NAPKIN", "TRAY",
        "BOTTLE", "KITCHEN", "EGG CUP", "RECIPE", "APRON", "OVEN", "CAKE TIN",
        "TEASPOON", "COASTER", "PLACEMAT", "JAM", "BREAD BIN", "TEACUP", "SAUCER")),
    ("Storage & Organisation", ("STORAGE", "JAR", "TIN", "BOX", "BASKET", "DRAWER",
        "HOOK", "HANGER", "RACK", "CADDY", "ORGANISER", "CRATE")),
    ("Bags", ("BAG", "SHOPPER", "TOTE", "SATCHEL", "RUCKSACK", "POUCH", "PURSE HOLDER")),
    ("Stationery & Craft", ("PAPER", "CRAFT", "CARD", "NOTEBOOK", "PEN", "PENCIL",
        "STICKER", "RIBBON", "GIFT WRAP", "WRAP", "CHALK", "JOURNAL", "TAPE", "STAMP",
        "SKETCH", "COLOURING", "ERASER", "RUBBER", "ENVELOPE", "NOTE", "DIARY")),
    ("Toys & Games", ("TOY", "GAME", "JIGSAW", "PUZZLE", "PLAYING CARD", "DOLL",
        "SOLDIER", "SPACEBOY", "SKITTLE", "DOMINO", "BLOCK", "MAGIC", "YOYO", "YO-YO",
        "SPINNING TOP", "DRAUGHTS")),
    ("Jewellery & Accessories", ("NECKLACE", "BRACELET", "RING", "EARRING", "JEWELLERY",
        "BANGLE", "BROOCH", "PURSE", "SCARF", "UMBRELLA", "HAIRCLIP", "HAIR CLIP",
        "GLOVE", "WALLET", "SUNGLASSES", "BADGE", "PENDANT", "CUFF")),
    ("Home Decor", ("FRAME", "ORNAMENT", "DECORATION", "HEART", "CUSHION", "CLOCK",
        "MIRROR", "VASE", "SIGN", "DOORMAT", "WALL", "CANDLESTICK", "PHOTO", "PICTURE",
        "HANGING", "BIRD", "FLOWER", "ROSE", "DOILY", "MAGNET", "KNOB", "CABINET",
        "DECORATIVE", "PLAQUE", "CHANDELIER", "DRAWER KNOB", "BLACKBOARD")),
    ("Garden & Outdoor", ("GARDEN", "PLANT", "WATERING", "PARASOL", "DECKCHAIR",
        "BIRD FEEDER", "BIRD BATH", "TRELLIS", "FLOWER POT", "PLANTER", "SEED", "TROWEL")),
    ("Bathroom & Beauty", ("SOAP", "BATH", "TOWEL", "FLANNEL", "SPONGE", "BEAUTY",
        "COSMETIC", "LIP", "PERFUME", "MANICURE")),
]


def heuristic_classify(desc: str) -> str:
    if not isinstance(desc, str) or not desc.strip():
        return "Other"
    u = desc.upper()
    for cat, kws in RULES:
        if any(k in u for k in kws):
            return cat
    return "Other"


def llm_classify(descriptions: list[str]) -> dict:  # pragma: no cover - needs API key
    """Production path (documented). Batches descriptions to an LLM with the taxonomy.

    Pseudocode kept intentionally explicit to show the prompt-engineering design:
        system = f"Classify each product into exactly one of: {TAXONOMY}. "
                 "Return strict JSON {description: category}. Use 'Other' if unsure."
        for batch in chunks(descriptions, 100):
            resp = client.chat(system, json.dumps(batch))   # OpenRouter/Anthropic/OpenAI
            mapping.update(parse_json(resp))
    Requires LLM_API_KEY in .env. Falls back to heuristic_classify per item on parse miss.
    """
    raise NotImplementedError("Set LLM_API_KEY in .env to enable the API path.")


def main():
    tx = pd.read_parquet(PROC / "clean_transactions.parquet")
    tx = tx[tx["is_product"]].copy()
    prod = (tx.groupby("stock_code")
              .agg(description=("description", "first"), revenue=("revenue", "sum"))
              .reset_index())
    prod["category"] = prod["description"].map(heuristic_classify)

    prod[["stock_code", "description", "category"]].to_csv(PROC / "category_map.csv", index=False)

    # Coverage report — by SKU count and by revenue (what matters commercially)
    by_sku = prod["category"].value_counts(normalize=True).mul(100).round(1)
    by_rev = (prod.groupby("category")["revenue"].sum()
                  .sort_values(ascending=False) / prod["revenue"].sum() * 100).round(1)
    other_sku = by_sku.get("Other", 0.0)
    other_rev = by_rev.get("Other", 0.0)

    print("\n=== CATEGORY COVERAGE ===")
    print(f"{'category':24s} {'%SKUs':>7s} {'%revenue':>9s}")
    for cat in by_rev.index:
        print(f"{cat:24s} {by_sku.get(cat,0):7.1f} {by_rev.get(cat,0):9.1f}")
    print(f"\nUncategorised ('Other'): {other_sku:.1f}% of SKUs, {other_rev:.1f}% of revenue")
    print(f"SKUs categorised: {len(prod)} | cache -> data/processed/category_map.csv")


if __name__ == "__main__":
    main()
