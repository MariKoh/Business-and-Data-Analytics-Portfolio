"""Build analysis-ready feature marts from the cleaned Online Retail II data.

Reads the raw workbook, cleans it via the shared steps in :mod:`src.data.clean`
(so the cleaning here is identical to the narrated Phase-1 notebook), and writes
three feature marts to ``data/processed/`` as Parquet:

1. ``customer_features.parquet``   - one row per Clubcard member (RFM + behaviour).
2. ``sku_timeseries.parquet``      - weekly quantity & revenue per product.
3. ``basket_transactions.parquet`` - one row per basket (item lists).

Run from the repository root::

    python -m src.pipeline.build_features

(In Phase 2 these marts are rebuilt as views over the DuckDB star schema; this
module remains the quick pandas path and the regression check for the cleaning.)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from src.data.clean import clean_transactions, load_raw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("build_features")


# --------------------------------------------------------------------------- #
# Feature marts
# --------------------------------------------------------------------------- #
def build_customer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Per-Clubcard-member RFM and behavioural features.

    Only transactions with a known Customer ID are used. Recency and tenure are
    measured against a snapshot date one day after the last transaction.
    """
    cust = df[df["customer_id"].notna()].copy()
    snapshot = cust["invoice_date"].max() + pd.Timedelta(days=1)
    log.info("customer_features: snapshot date = %s", snapshot.date())

    feats = cust.groupby("customer_id").agg(
        first_purchase=("invoice_date", "min"),
        last_purchase=("invoice_date", "max"),
        frequency=("invoice", "nunique"),
        total_quantity=("quantity", "sum"),
        monetary=("revenue", "sum"),
        num_distinct_skus=("stock_code", "nunique"),
    )
    feats["recency_days"] = (snapshot - feats["last_purchase"]).dt.days
    feats["tenure_days"] = (snapshot - feats["first_purchase"]).dt.days
    feats["avg_basket_value"] = feats["monetary"] / feats["frequency"]
    feats["avg_items_per_basket"] = feats["total_quantity"] / feats["frequency"]
    feats = feats.reset_index()

    cols = [
        "customer_id", "recency_days", "frequency", "monetary",
        "total_quantity", "num_distinct_skus", "tenure_days",
        "avg_basket_value", "avg_items_per_basket",
        "first_purchase", "last_purchase",
    ]
    feats = feats[cols]
    log.info("Built customer_features: %s members x %d columns.",
             f"{len(feats):,}", feats.shape[1])
    return feats


def build_sku_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """Weekly quantity & revenue per product (active weeks only; product lines)."""
    prod = df[df["is_product"]].copy()
    prod["week"] = (
        prod["invoice_date"].dt.normalize()
        - pd.to_timedelta(prod["invoice_date"].dt.weekday, unit="D")
    )

    weekly = (
        prod.groupby(["stock_code", "week"])
        .agg(quantity=("quantity", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    desc = (
        prod.dropna(subset=["description"])
        .groupby(["stock_code", "description"]).size()
        .reset_index(name="n")
        .sort_values(["stock_code", "n"], ascending=[True, False])
        .drop_duplicates("stock_code")
        .set_index("stock_code")["description"]
    )
    weekly["description"] = weekly["stock_code"].map(desc).astype("string")
    weekly = (
        weekly[["stock_code", "description", "week", "quantity", "revenue"]]
        .sort_values(["stock_code", "week"])
        .reset_index(drop=True)
    )
    log.info("Built sku_timeseries: %s SKUs, %s weekly rows.",
             f"{weekly['stock_code'].nunique():,}", f"{len(weekly):,}")
    return weekly


def build_basket_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """One row per basket (Invoice): distinct product list and basket totals."""
    prod = df[df["is_product"]].copy()
    grp = prod.groupby("invoice")
    basket = grp.agg(
        invoice_date=("invoice_date", "min"),
        customer_id=("customer_id", "first"),
        country=("country", "first"),
        n_lines=("stock_code", "size"),
        n_distinct_items=("stock_code", "nunique"),
        basket_revenue=("revenue", "sum"),
    )
    items = grp["stock_code"].agg(lambda s: sorted(set(s))).rename("items")
    basket = basket.join(items).reset_index()
    basket = basket[[
        "invoice", "invoice_date", "customer_id", "country",
        "n_lines", "n_distinct_items", "basket_revenue", "items",
    ]]
    log.info("Built basket_transactions: %s baskets.", f"{len(basket):,}")
    return basket


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _write_summary(clean: pd.DataFrame, customer: pd.DataFrame,
                   sku: pd.DataFrame, basket: pd.DataFrame) -> dict:
    """Write a small JSON summary used by the report and the recommendations."""
    summary = {
        "clean_transaction_lines": int(len(clean)),
        "date_range_start": str(clean["invoice_date"].min().date()),
        "date_range_end": str(clean["invoice_date"].max().date()),
        "n_customers": int(customer["customer_id"].nunique()),
        "n_products": int(sku["stock_code"].nunique()),
        "n_baskets": int(len(basket)),
        "total_revenue": round(float(clean.loc[clean["is_product"], "revenue"].sum()), 2),
        "countries": int(clean["country"].nunique()),
    }
    out = PROCESSED_DIR / "dataset_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    log.info("Wrote dataset summary -> %s", out.name)
    return summary


def main() -> None:
    """Run the full mart build: raw xlsx -> three processed Parquet tables."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    clean = clean_transactions(load_raw())
    clean.to_parquet(PROCESSED_DIR / "clean_transactions.parquet", index=False)
    log.info("Wrote clean_transactions.parquet (%s lines) for downstream phases.",
             f"{len(clean):,}")

    customer = build_customer_features(clean)
    sku = build_sku_timeseries(clean)
    basket = build_basket_transactions(clean)

    customer.to_parquet(PROCESSED_DIR / "customer_features.parquet", index=False)
    sku.to_parquet(PROCESSED_DIR / "sku_timeseries.parquet", index=False)
    basket.to_parquet(PROCESSED_DIR / "basket_transactions.parquet", index=False)
    log.info("Wrote 3 feature marts to %s", PROCESSED_DIR)

    summary = _write_summary(clean, customer, sku, basket)
    log.info("Pipeline summary: %s", json.dumps(summary))
    log.info("DONE.")


if __name__ == "__main__":
    main()
