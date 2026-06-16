"""
Modelling cleanse - stricter than analytics `clean_transactions`, per Koh's rules.
Leaves the raw untouched; writes a SEPARATE file: data/processed/model_transactions.parquet

Rules (tuned for modelling):
  * exact duplicate rows           -> REMOVE
  * non-positive quantity / price  -> REMOVE  (adjustments, freebies, write-offs;
        this also clears the negative-qty cancellation lines)
  * service / admin codes (POST..) -> REMOVE  (keep genuine SKUs only)
  * missing Customer ID            -> KEEP, labelled member_status = "Non-Member"
        (guest baskets are real demand and the loyalty-conversion target; customer-level
         models still use Members only, since anonymous rows are not one customer)
  * missing product description    -> KEEP    (left as-is)

Shares the cleaning functions from clean.py where they apply (no logic drift).
Run:  python -m src.data.clean_for_model
"""
from __future__ import annotations
import logging
from pathlib import Path
import pandas as pd

from src.data.clean import (
    PRODUCT_CODE_PATTERN,
    standardise_dtypes, drop_duplicate_rows, drop_nonpositive, add_revenue,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("clean_for_model")

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
RAW_CACHE = PROC / "raw_concat.parquet"
OUT = PROC / "model_transactions.parquet"


def keep_products_only(df: pd.DataFrame) -> pd.DataFrame:
    """Modelling rule: drop service/admin codes (POST, DOT, D, M, ADJUST, ...)."""
    before = len(df)
    out = df[df["stock_code"].str.match(PRODUCT_CODE_PATTERN)]
    log.info("Dropped %s service/admin lines (kept genuine SKUs).", f"{before - len(out):,}")
    return out


def label_member_status(df: pd.DataFrame) -> pd.DataFrame:
    """Modelling rule: KEEP guest rows, label Member vs Non-Member (do not drop)."""
    df = df.copy()
    df["member_status"] = df["customer_id"].notna().map({True: "Member", False: "Non-Member"})
    n_non = int((df["member_status"] == "Non-Member").sum())
    log.info("Labelled %s Non-Member rows (kept, not dropped).", f"{n_non:,}")
    return df


MODEL_STEPS = [
    ("standardise dtypes", standardise_dtypes),
    ("drop duplicate rows", drop_duplicate_rows),
    ("drop non-positive qty/price", drop_nonpositive),
    ("drop service/admin codes", keep_products_only),
    ("label member status (keep guests)", label_member_status),
    ("add line revenue", add_revenue),
]


def main():
    raw = pd.read_parquet(RAW_CACHE)
    n0 = len(raw)
    df = raw.copy()
    audit = []
    for label, step in MODEL_STEPS:
        before = len(df)
        df = step(df)
        audit.append({"step": label, "rows_in": before, "rows_out": len(df),
                      "removed": before - len(df)})
    df = df.reset_index(drop=True)
    df.to_parquet(OUT, index=False)

    # Member vs Non-Member opportunity sizing
    g = df.groupby("member_status").agg(
        rows=("invoice", "size"),
        baskets=("invoice", "nunique"),
        revenue=("revenue", "sum"),
    )
    g["avg_basket_value"] = (g["revenue"] / g["baskets"]).round(2)
    g["revenue_pct"] = (g["revenue"] / g["revenue"].sum() * 100).round(1)

    print("\n=== MODELLING CLEANSE AUDIT ===")
    print(pd.DataFrame(audit).to_string(index=False))
    print(f"\nRaw {n0:,} -> modelling {len(df):,} ({100*len(df)/n0:.1f}% retained)")
    print("\n=== MEMBER vs NON-MEMBER (loyalty conversion opportunity) ===")
    print(g.to_string())
    print(f"\nSaved -> {OUT.relative_to(ROOT)} (raw + clean_transactions untouched)")
    print("Note: customer-level models (segmentation/churn/CLV) use Members only.")


if __name__ == "__main__":
    main()
