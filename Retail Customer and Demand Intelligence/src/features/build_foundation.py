"""
Feature foundation - the shared, reusable layer that sits between cleansing and modelling.

Source-of-truth (deliberate, see README 'Data lineage'):
  * customer_features   <- model_transactions   (identified customers; customer models)
  * sku_timeseries      <- clean_transactions    (products; KEEP guest demand)
  * basket_transactions <- clean_transactions    (products; KEEP guest baskets)
  * product_master      <- clean products + category_map  (LLM-derived category)
  * category is joined onto all product-level data.

Reuses the exact mart builders from src/pipeline/build_features (no logic drift) and
only re-points the source and adds the category dimension.

Model-specific features (forecasting lags/calendar, churn time-split label, basket
co-occurrence) are built WITH each model, not here.

Run:  python -m src.features.build_foundation
"""
from __future__ import annotations
import json, logging
from pathlib import Path
import pandas as pd

from src.pipeline.build_features import (
    build_customer_features, build_sku_timeseries, build_basket_transactions,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("foundation")

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"


def build_product_master(clean: pd.DataFrame, catmap: pd.DataFrame) -> pd.DataFrame:
    prod = clean[clean["is_product"]]
    agg = prod.groupby("stock_code").agg(
        total_quantity=("quantity", "sum"),
        total_revenue=("revenue", "sum"),
        n_orders=("invoice", "nunique"),
    ).reset_index()
    master = catmap.merge(agg, on="stock_code", how="left")
    return master


def main():
    clean = pd.read_parquet(PROC / "clean_transactions.parquet")
    model = pd.read_parquet(PROC / "model_transactions.parquet")
    catmap = pd.read_csv(PROC / "category_map.csv", dtype={"stock_code": "string"})

    # 1. customer_features  <- model_transactions
    customer = build_customer_features(model)

    # 2/3. sku_timeseries & basket  <- clean products (guest-inclusive), + category
    sku = build_sku_timeseries(clean)
    sku["stock_code"] = sku["stock_code"].astype("string")
    sku = sku.merge(catmap[["stock_code", "category"]], on="stock_code", how="left")
    sku["category"] = sku["category"].fillna("Other")

    basket = build_basket_transactions(clean)

    # 4. product_master with category
    master = build_product_master(clean, catmap)

    customer.to_parquet(PROC / "customer_features.parquet", index=False)
    sku.to_parquet(PROC / "sku_timeseries.parquet", index=False)
    basket.to_parquet(PROC / "basket_transactions.parquet", index=False)
    master.to_parquet(PROC / "product_master.parquet", index=False)

    cat_cov = sku.groupby("category")["revenue"].sum().sort_values(ascending=False)
    cat_cov_pct = (cat_cov / cat_cov.sum() * 100).round(1)

    summary = {
        "customer_features_source": "model_transactions",
        "customer_features_rows": int(len(customer)),
        "sku_timeseries_source": "clean_transactions (products, guest-inclusive)",
        "sku_timeseries_skus": int(sku["stock_code"].nunique()),
        "basket_source": "clean_transactions (products, guest-inclusive)",
        "baskets": int(len(basket)),
        "product_master_skus": int(len(master)),
    }
    (PROC / "foundation_summary.json").write_text(json.dumps(summary, indent=2))

    print("\n=== FEATURE FOUNDATION ===")
    print(f"customer_features : {len(customer):>9,} members   (source: model_transactions)")
    print(f"sku_timeseries    : {sku['stock_code'].nunique():>9,} SKUs, {len(sku):,} rows  (source: clean products + category)")
    print(f"basket_transactions:{len(basket):>9,} baskets    (source: clean products)")
    print(f"product_master    : {len(master):>9,} SKUs with category")
    print("\nsku_timeseries revenue by category (%):")
    for c, v in cat_cov_pct.items():
        print(f"   {c:24s} {v:5.1f}")
    print("\nsaved 4 marts + foundation_summary.json -> data/processed/")


if __name__ == "__main__":
    main()
